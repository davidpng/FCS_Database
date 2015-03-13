from FlowAnal.FlowQC import FlowQC
import pandas as pd
import numpy as np
from scipy import odr
import logging
log = logging.getLogger(__name__)
from matplotlib import pyplot as plt
import itertools
from pyemd import emd
from multiprocessing import Pool
from math import floor


class Flow_Comparison(object):
    """ Compare QC data across samples """
    def __init__(self, args, dbcon):
        if args.comparison == 'global':
            self.Global_Comparisons(args, dbcon)
        elif args.comparison == 'peaks':
            self.Peak_Comparisons(args, dbcon)
        else:
            raise ValueError('Comparison {} is not valid'.format(args.comparison))

    def Global_Comparisons(self, args, dbcon, **kwargs):
        """ Compare distributions globally """

        # Get options
        workers = args.workers
        split_array_factor = args.split_array_factor

        # Collect cross-data
        a = FlowQC(dbcon=dbcon, make_qc_data=False)
        (df, name) = a.get_1D_intensities(**vars(args))

        # Pick cases
        cases = df.copy()
        cases = cases.drop(['bin', 'density'], axis=1)
        cases = cases.drop_duplicates()
        cases.sort(['date', 'case_tube_idx'], inplace=True)
        cases['order'] = range(cases.shape[0])
        cases.sort(['case_number', 'tube_type', 'case_tube_idx'], inplace=True)

        ctis = cases.groupby(['case_number']).\
                filter(lambda x: len(np.unique(x['tube_type'].values)) > 1)
        ctis = ctis.groupby(['case_number', 'tube_type']).tail(1)
        df = pd.merge(df, ctis[['case_tube_idx']], left_on=['case_tube_idx'],
                      right_on=['case_tube_idx'], how='right')
        df.set_index(['case_tube_idx', 'bin'], inplace=True)
        df.sort_index(inplace=True)

        nsamples = ctis.shape[0]
        log.info('Found {} ctis'.format(nsamples))
        xs = [x for x in itertools.product(range(0, nsamples), repeat=2)]
        xs = zip(*xs)
        same_case = ctis.case_number.values[[xs[0]]] == ctis.case_number.values[[xs[1]]]
        same_cyt = ctis.cytnum.values[[xs[0]]] == ctis.cytnum.values[[xs[1]]]
        same_assay = ctis.tube_type.values[[xs[0]]] == ctis.tube_type.values[[xs[1]]]
        seconds_diff = abs(ctis.date.values[[xs[0]]] - ctis.date.values[[xs[1]]]) / np.timedelta64(1, 's')
        order_diff = abs(ctis.order.values[[xs[0]]] - ctis.order.values[[xs[1]]])
        sample_comps = pd.DataFrame({'ctiA': ctis.case_tube_idx.values[[xs[0]]],
                                     'ctiB': ctis.case_tube_idx.values[[xs[1]]],
                                     'case': same_case,
                                     'cyt': same_cyt,
                                     'assay': same_assay,
                                     'seconds_diff': seconds_diff,
                                     'order_diff': order_diff})
        sample_comps['same_day'] = sample_comps.seconds_diff < (60 * 60 * 24)

        log.info('Calculating EMD')

        # Setup data
        densities = df[['density']]
        densities = densities.unstack()
        ctis = densities.index.values
        densities = densities.values

        if split_array_factor is not None:
            new_bin_num = floor(100 / split_array_factor)
            new_densities = [np.sum(x, axis=1)
                             for x in np.split(densities, new_bin_num, axis=1)]
            densities = np.vstack(new_densities).T
            densities.shape = (len(ctis), new_bin_num)
            densities = densities.copy(order='C')

        #  Make bin distance array
        bins = np.linspace(0, densities.shape[1], densities.shape[1])
        bin_dist = [abs(x[0] - x[1]) for x in itertools.product(bins, repeat=2)]
        bin_dist = np.asarray(bin_dist)
        bin_dist.shape = (densities.shape[1], densities.shape[1])
        log.debug('Density matrix is size {}'.format(densities.shape))

        emd_dists = []
        if workers is not None:
            p = Pool(workers)
            emd_dists = [p.apply_async(calc_emd,
                                       args=(densities, i, bin_dist, args.linear_align))
                         for i in range(len(ctis))]
            log.info('Made {} jobs'.format(len(emd_dists)))
            p.close()
        else:
            for i in range(len(ctis)):
                emd_dists.append(calc_emd(densities, i, bin_dist, args.linear_align))
                log.info('Made {} jobs'.format(len(emd_dists)))

        a_df = pd.DataFrame({}, columns=['ctiA', 'ctiB', 'emd_dist'])
        for x in emd_dists:
            print "Processed {} of {}\r".format(a_df.shape[0], sample_comps.shape[0]),
            if workers is not None:
                x_df = pd.DataFrame(x.get(), columns=['ctiA', 'ctiB', 'emd_dist'])
            else:
                x_df = pd.DataFrame(x, columns=['ctiA', 'ctiB', 'emd_dist'])
            x_df.ctiA = ctis[[x_df.ctiA.values]]
            x_df.ctiB = ctis[[x_df.ctiB.values]]
            a_df = pd.concat([a_df, x_df])

        a_df.ctiA = a_df.ctiA.astype(int)
        a_df.ctiB = a_df.ctiB.astype(int)
        sample_comps = pd.merge(sample_comps, a_df, left_on=['ctiA', 'ctiB'],
                                right_on=['ctiA', 'ctiB'], how='left')
        sample_comps.to_csv(''.join([args.outp, name, 'emd.txt']), sep="\t")

    def Peak_Comparisons(self, args, dbcon, **kwargs):
        """ Identify peaks across one variable and compare peak locations by Deming Regression """

        # Collect cross-data
        compvars = getattr(args, args.crossanal)
        d = []
        for var in compvars:
            setattr(args, args.crossanal, [var])
            a = FlowQC(dbcon=dbcon, make_qc_data=False)
            (df, name) = a.get_1D_intensities(**vars(args))

            # if args.add_beads is True:
            #     # Have to apply this earlier
            #     beads_df = a.get_beads(**vars(args))

            #     # Simplification
            #     beads_df = beads_df.loc[beads_df.peak == 'P8', :]  # Pick #8
            #     beads_df.drop(['peak'], axis=1, inplace=True)

            #     mean_beadMFI = beads_df.MFI.mean()

            #     beads_df['day'] = pd.DatetimeIndex(beads_df.date).date.astype(str)
            #     beads_df.drop(['date'], axis=1, inplace=True)

            #     df['day'] = pd.DatetimeIndex(df.date).date.astype(str)
            #     df = pd.merge(df, beads_df, how='left', left_on=['day', 'cytnum', 'Fluorophore'],
            #                   right_on=['day', 'cytnum', 'Fluorophore'])

            #     # Normalize
            #     print df.head()
            #     df.density = np.divide(df.density, df.MFI) * mean_beadMFI

            print df.head()
            quit()
            peaks_df = a.add_peaks(df=df, name=name, **vars(args))
            peaks_df.index = [int(x) for x in peaks_df.index]

            cases = df[['case_tube_idx', 'case_number']].drop_duplicates()
            cases.sort(['case_number', 'case_tube_idx'], inplace=True)
            cases = cases.groupby(['case_number']).tail(1)  # Pick highest cti

            peaks_df = pd.merge(cases, peaks_df,
                                left_on='case_tube_idx', right_index=True,
                                how='inner')
            peaks_df[args.crossanal] = var
            peaks_df.drop(['case_tube_idx'], axis=1, inplace=True)
            d.append(peaks_df)
        df = pd.concat(d)
        df.set_index(['case_number', args.crossanal], inplace=True)

        # Compare cross-data
        for p in df:
            p_df = df[[p]]
            p_df = p_df.unstack()
            p_df = p_df.loc[np.all(~p_df.isnull(), axis=1), :]
            name = '_'.join(args.antigens + compvars + args.cytnum + [p])

            # Exclude outliers
            rolling_mean = pd.rolling_mean(p_df, 20, center=True, min_periods=1)
            rolling_sd = pd.rolling_std(p_df, 20, center=True, min_periods=1)

            p_df = p_df.loc[~np.any((p_df > (rolling_mean + 2.5 * rolling_sd)) |
                                    ((p_df < rolling_mean - 2.5 * rolling_sd)), axis=1), :]

            x = p_df[p, compvars[0]].values
            y = p_df[p, compvars[1]].values

            p_df.to_csv(''.join([args.outp, name, '.txt']), sep="\t")

            def f(B, x):
                return B[0]*x + B[1]

            def finv(B, y):
                return (y - B[1])/B[0]

            linear = odr.Model(f)
            mydata = odr.Data(x, y)
            myodr = odr.ODR(mydata, linear, beta0=[1., 0.])
            fit = myodr.run()
            xlfit = np.linspace(min(x), max(x), len(x) * 10)
            ylfit = f(fit.beta, xlfit)
            yfit = f(fit.beta, x)
            xfit = finv(fit.beta, y)
            TSS_x = np.sum((x - np.mean(x))**2)
            TSS_y = np.sum((y - np.mean(y))**2)

            RSS_x = np.sum((x - xfit)**2)
            RSS_y = np.sum((y - yfit)**2)

            x_r2 = 1 - RSS_x/TSS_x
            y_r2 = 1 - RSS_y/TSS_y
            log.info('Fit with coeff {} and R^2[x] {:.2f}  R^2[y] {:.2f} '.format(fit.beta,
                                                                                  x_r2,
                                                                                  y_r2))
            fig = plt.figure(figsize=(6, 6))
            ax = fig.add_subplot(111)
            plt.title(name)
            plt.xlabel(p_df.columns[0][1])
            plt.ylabel(p_df.columns[1][1])
            ax.plot(xlfit, ylfit,
                    color='orange', linestyle='-')
            ax.plot(np.linspace(min(x), max(x), 10), np.linspace(min(x), max(x), 10),
                    color='black', linestyle='--')
            ax.plot(x, y, 'ro', alpha=0.3)
            plt.text(0.1, 0.8,
                     "Coeffs: {}\nR2[x]: {:.2f}\nR2[y]: {:.2f}".format(fit.beta,
                                                                       x_r2,
                                                                       y_r2),
                     transform=ax.transAxes)
            plt.savefig('_'.join([args.outp, name]) + '.png',
                        bbox_inches='tight', dpi=200)
            plt.close()


def calc_emd(densities, i, bin_dist, linear_align=False, max_allowable_shift=np.Inf):
    """ Calculate and return emd distance between row i and all other rows in densities

    * linear_align: linear shift of two arrays based on max cross-correlation
    * max_allowable_shift: The maximum linear shift that is permissible
    """
    results = []
    a = densities[i, :]
    no_shift = int(len(a) - 1)
    for j in range(densities.shape[0]):
        a2 = a.copy()
        b = densities[j, :]

        if linear_align is True:
            max_shift = int(np.argmax(np.correlate(a2, b, mode='full')))
            to_pad = max_shift - no_shift
            to_shift = abs(int(floor(to_pad/2)))
            if 0 < to_pad <= max_allowable_shift:
                a2 = np.pad(a2, (0, to_pad),
                            'constant', constant_values=0)[to_shift:(len(a) + to_shift)]
                b = np.pad(b, (to_pad, 0),
                           'constant', constant_values=0)[to_shift:(to_shift+len(a))]
            elif (-1 * max_allowable_shift) <= to_pad < 0:
                a2 = np.pad(a2, (-to_pad, 0),
                            'constant', constant_values=0)[to_shift:(len(a) + to_shift)]
                b = np.pad(b, (0, -to_pad),
                           'constant', constant_values=0)[to_shift:(to_shift+len(a))]
            log.debug("Shifted {} => {}".format((max_shift, to_pad),
                                                np.argmax(np.correlate(a2, b, mode='full'))))

        results.append((i, j,
                        emd(a2, b, bin_dist)))
    return results
