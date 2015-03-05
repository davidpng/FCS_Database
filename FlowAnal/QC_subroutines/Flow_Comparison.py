from FlowAnal.FlowQC import FlowQC
import pandas as pd
import numpy as np
from scipy import odr
import logging
log = logging.getLogger(__name__)
from matplotlib import pyplot as plt


class Flow_Comparison(object):
    """ Compare QC data across samples """
    def __init__(self):
        pass

    def Peak_Comparisons(self, args, dbcon, **kwargs):
        """ Identify peaks across one variable and compare peak locations by Deming Regression """

        # Collect cross-data
        compvars = getattr(args, args.crossanal)
        d = []
        for var in compvars:
            setattr(args, args.crossanal, [var])
            a = FlowQC(dbcon=dbcon, make_qc_data=False)
            (df, name) = a.get_1D_intensities(**vars(args))
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

