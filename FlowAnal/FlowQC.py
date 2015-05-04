import pandas as pd
import numpy as np
np.set_printoptions(precision=2)

import matplotlib as mplt
from matplotlib import pyplot as plt
from math import ceil
import brewer2mpl
from datetime import datetime, time, timedelta
import logging
log = logging.getLogger(__name__)

from QC_subroutines.Peaks_1D import Peaks_1D, Peaks_1D_Set
from FlowAnal.FCS_subroutines.Process_FCS_Data import LogicleTransform


def normalize_timeseries(df, time_quantile=5, **kwargs):
    """ Normalize a timeseries pandas data frame and return new df"""
    dates = np.unique(zip(*df.index.values)[0])
    tds = np.diff(dates)
    get_seconds = np.vectorize(lambda x: x.seconds, otypes=[np.int32])
    tds = get_seconds(tds)
    ival = int(10 * round(np.percentile(tds, time_quantile) / (60 * 10)))
    rng = pd.date_range(start=datetime.combine(min(dates).date(), time()),
                        end=datetime.combine(max(dates).date() +
                                             timedelta(days=1), time()),
                        freq=str(ival) + 'min', tz=None)
    df2 = df.reindex(index=rng, level='date', copy=True, method='ffill').dropna()

    # Need to widen the dataframe and then maybe tallify again???
    print df2.head()
    quit()
    return df2


def flow_transform(x):
    """ Transform and rescale numpy array """

    x = LogicleTransform(x, A=0)  # Transform
    x = x / np.float(2**18)  # Scale
    x = (x - (-0.15)) / (1.0 - (-0.15))  # Rescale
    x *= 100
    return x


class FlowQC(object):
    """ Class to encapsulate QC of flow data

    Keyword arguments:
    db  -- FCS_Database object that contains histos and stats
    """

    def __init__(self, dbcon, outdbcon=None, testing=False,
                 make_qc_data=True, **kwargs):
        self.db = dbcon
        self.outdb = outdbcon

        if make_qc_data is True:
            # Load all QC data
            if testing is True and outdbcon is not None:
                self.__make_flat_db('TubeStats', index=['date'],
                                    normalize_time=False, **kwargs)
                self.__make_histos(**kwargs)
                self.__make_flat_db('PmtStats', index=['date', 'Channel_Number'],
                                    normalize_time=False, **kwargs)
                self.__make_flat_db('PmtCompCorr', index=['date', 'Channel_Number'],
                                    normalize_time=False, **kwargs)
            else:
                self.TubeStats = self.__get_query_res('TubeStats', index=['date'],
                                                      normalize_time=False,
                                                      **kwargs)
                self.PmtStats = self.__get_query_res('PmtStats',
                                                        index=['date', 'Channel_Number'],
                                                        normalize_time=False,
                                                        **kwargs)
                self.PmtCompCorr = self.__get_query_res('PmtCompCorr',
                                                        index=['date', 'Channel_Number'],
                                                        normalize_time=False,
                                                        **kwargs)

    def __make_histos(self, table_format='tall', normalize_time=False, **kwargs):
        """ Return pandas df from db table PmtHistos

        NOTE:
        - Adds NAs to densities not present in database table
        """
        dq = self.db.query(getPmtHistos=True, **kwargs)

        i = 0
        for df in pd.read_sql_query(sql=dq.qstring,
                                    con=self.db.engine,
                                    params=dq.params, chunksize=10000):
            i += df.shape[0]

            if normalize_time is True:
                df.set_index('date', drop=True, inplace=True)
                df = normalize_timeseries(df, **kwargs)
            elif table_format == 'wide':
                meta_cols = [c for c in df.columns if c not in ['density']]
                df.set_index(meta_cols, inplace=True)
                df = df.unstack()
                df.reset_index(drop=False, inplace=True, col_level=0)

                # Fix column names
                new_columns = []
                for i in range(len(df.columns)):
                    if df.columns[i][1] == '':
                        new_columns.append(df.columns[i][0])
                    else:
                        new_columns.append(df.columns[i][1])
                df.columns = new_columns

            df.to_sql('full_' + 'PmtHistos',
                      con=self.outdb.engine,
                      if_exists='append',
                      index=False)

    def __get_query_res(self, goal, index=['date'], normalize_time=False, **kwargs):
        """ Return pandas df from db table specified by goal """
        kwargs['get' + goal] = True
        df = self.db.query(**kwargs).results

        if normalize_time is True:
            df.set_index(index, drop=False, inplace=True)
            df2 = normalize_timeseries(df, **kwargs)
            return df2
        else:
            return df

    def __make_flat_db(self, goal, index=['date'], normalize_time=False, **kwargs):
        """ Query for stats and push to new db """
        kwargs['get' + goal] = True
        dq = self.db.query(**kwargs)

        i = 0
        for df in pd.read_sql_query(sql=dq.qstring,
                                    con=self.db.engine,
                                    params=dq.params, chunksize=10000):
            i += df.shape[0]
            df.to_sql('full_' + goal,
                      con=self.outdb.engine,
                      if_exists='append',
                      index=False)

    def get_1D_intensities(self, **kwargs):
        """ Pull 1D histogram (PmtHistos) for single channel/antigen/...

        Return tuple of df and name
        """

        kwargs['getPmtHistos'] = True
        dq = self.db.query(**kwargs)
        kwargs['getPmtHistos'] = None
        log.debug("Query: [{}]".format(dq.qstring))
        log.info("Query result count: {}".format(dq.q.count()))

        df = pd.read_sql_query(sql=dq.qstring,
                               con=self.db.engine,
                               params=dq.params)
        df.sort(['date', 'case_number', 'case_tube_idx', 'bin'], inplace=True)
        log.debug("Size of df: {}".format(df.shape))

        # Make name base
        name = ""
        for k in ['tubes', 'antigens', 'fluorophores', 'Channel_Name', 'Channel_Number',
                  'cytnum', 'daterange']:
            if k in kwargs and kwargs[k] is not None:
                if name == "":
                    name = "_".join(str(x) for x in kwargs[k])
                else:
                    name = "{}_{}".format(name, "_".join(str(x) for x in kwargs[k]))
        return (df, name)

    def process_compensation(self, **kwargs):
        """

        """
        kwargs['getPmtCompCorr'] = True
        dq = self.db.query(get_fluorophore_list=True, **kwargs)
        kwargs['getPmtCompCorr'] = None

        df = pd.read_sql_query(sql=dq.qstring,
                               con=self.db.engine,
                               params=dq.params)
        fluorophores = [x for x in df.Fluorophore.unique()
                        if x not in [None, 'TIME']]
        log.info('Using fluorophores {}'.format(fluorophores))

        for cytnum in [1, 2]:
            for f in fluorophores:
                kwargs['fluorophores'] = [f]
                kwargs['cytnum'] = [cytnum]
                (df, name) = self.__get_compensation_histogram(**kwargs)
                df.sort(['Fluorophore_FROM', 'date'], inplace=True)

                if len(df) > 100:
                    self.__plot_compensation(df, name='.'.join([kwargs['outp'], name]),
                                             **kwargs)
                kwargs['fluorophores'] = None
                kwargs['cytnum'] = None

    def __plot_compensation(self, df, name, win=30, **kwargs):
        """
        """
        # Plot
        fsize = (max(ceil(df.shape[0]/4000), 12.5*3),
                 max(ceil(df.shape[0]/20000), 5*3))
        plt.figure(figsize=fsize)
        plt.title(name)

        # TODO: add moving average
        df_c = df.copy()
        df_c = df_c.groupby(['Fluorophore_FROM']).filter(lambda x: len(x) > 10)
        df_cg = df_c.groupby(['Fluorophore_FROM'])

        leg_handles = []
        for g, dfg in df_cg:
            rm = pd.stats.moments.rolling_median(dfg.Pearson_R,
                                                 window=win, center=True, min_periods=win/2)
            leg_handle, = plt.plot(dfg.date, rm, '-',
                                   scalex=True, scaley=False, label=g)
            leg_handles.append(leg_handle)

        plt.legend(handles=leg_handles, loc=4)

        plt.savefig(name + '.png', bbox_inches='tight', dpi=200)
        plt.close()

    def __get_compensation_histogram(self, **kwargs):
        """ Pull Compensation cross-talk matrix for single channel/antigen/...

        Return tuple of df and name
        """

        non_fluos = ['TIME', 'FSC-A', 'FSC-H', 'SSC-H', 'SSC-A', None]
        kwargs['getPmtCompCorr'] = True
        dq = self.db.query(**kwargs)
        kwargs['getPmtCompCorr'] = None

        log.debug("Query: [{}]".format(dq.qstring))
        log.info("Query result count: {}".format(dq.q.count()))

        df = pd.read_sql_query(sql=dq.qstring,
                               con=self.db.engine,
                               params=dq.params)
        df = df.loc[~df.Fluorophore_IN.isin(non_fluos), :]
        df.sort(['date', 'cytnum'], inplace=True)
        log.debug("Size of df: {}".format(df.shape))

        # Make name base
        name = ""
        for k in ['tubes', 'fluorophores', 'antigens', 'Channel_Name', 'Channel_Number',
                  'cytnum', 'daterange']:
            if k in kwargs and kwargs[k] is not None:
                if name == "":
                    name = "_".join(str(x) for x in kwargs[k])
                else:
                    name = "{}_{}".format(name, "_".join(str(x) for x in kwargs[k]))
        return (df, name)

    def get_beads_8peak(self, smooth=False,
                        **kwargs):

        # Setup query
        kwargs['getbeads_8peaks'] = True
        dq = self.db.query(**kwargs)
        log.debug("Query: [{}] with params [{}]".format(dq.qstring, dq.params))
        log.info("Query result count: {}".format(dq.q.count()))

        # Get table
        df = pd.read_sql_query(sql=dq.qstring,
                               con=self.db.engine,
                               params=dq.params,
                               parse_dates=None)

        # Select dates
        df.date = df.date.astype(np.datetime64)
        df.drop(['id'], inplace=True, axis=1)
        df = df.loc[(df.date >= np.datetime64(kwargs['daterange'][0])) &
                    (df.date <= np.datetime64(kwargs['daterange'][1])), :]

        df.sort(['cytnum', 'date', 'Fluorophore', 'peak'], inplace=True)

        df.MFI = flow_transform(df.MFI.values)

        if smooth is True:
            bead_df2 = []
            bdg = df.groupby(['cytnum', 'Fluorophore', 'peak'])
            for name, g in bdg:
                g.MFI = pd.rolling_mean(g.MFI,
                                        window=5,
                                        center=True,
                                        min_periods=1)
                bead_df2.append(g)
            df = pd.concat(bead_df2)

        return df

    def calc_sds(self, df):
        """ Assume CV calculated on transformed data """

        mean = flow_transform(df.Mean.values)
        # mean_ps = flow_transform(df.Mean.values * (1 + df.CV.values/100))
        # mean_ms = flow_transform(df.Mean.values - (1 + df.CV.values/100))
        # df['Mean_ms'] = mean_ms
        df.Mean = mean
        # df['Mean_ps'] = mean_ps
        return df

    def get_beads_ultra(self, smooth=False,
                        **kwargs):

        # Setup query
        kwargs['getbeads_ultra'] = True
        dq = self.db.query(**kwargs)
        log.debug("Query: [{}] with params [{}]".format(dq.qstring, dq.params))
        log.info("Query result count: {}".format(dq.q.count()))

        # Get table
        df = pd.read_sql_query(sql=dq.qstring,
                               con=self.db.engine,
                               params=dq.params,
                               parse_dates=None)


        # Select dates
        df.date = df.date.astype(np.datetime64)
        df.drop(['id'], inplace=True, axis=1)
        df = df.loc[(df.date >= np.datetime64(kwargs['daterange'][0])) &
                    (df.date <= np.datetime64(kwargs['daterange'][1])), :]

        df.sort(['cytnum', 'date', 'Fluorophore'], inplace=True)

        df = self.calc_sds(df)
        df.rename(columns={'Mean': 'MFI'}, inplace=True)

        if smooth is True:
            bead_df2 = []
            bdg = df.groupby(['cytnum', 'Fluorophore'])
            for name, g in bdg:
                g.MFI = pd.rolling_mean(g.MFI,
                                         window=5,
                                         center=True,
                                         min_periods=1)
                g.CV = pd.rolling_mean(g.CV,
                                       window=5,
                                       center=True,
                                       min_periods=1)
                bead_df2.append(g)
            df = pd.concat(bead_df2)

        return df

    def add_peaks(self, df, name='test',
                  trim_peaks=False, peak_detector='local_max',
                  beads_df=None,
                  **kwargs):
        """ Find peaks, and label

        Output should be df of tube_case_idx, Channel_Number, PEAK_ID, intensity (scaled)
        """

        df.sort(['date', 'case_tube_idx', 'bin'], inplace=True)
        ctis = df.case_tube_idx.unique()   # In order

        all_peaks = Peaks_1D_Set(name=name)
        for i, cti in enumerate(ctis):
            d = df.loc[df.case_tube_idx == cti, 'density'].values
            iname = "{}_{}".format(name, str(cti))

            if len(d) != 100:
                raise ValueError('Length of vector for {} is {} rather than 100'.format(cti,
                                                                                        len(d)))
            peaks = Peaks_1D(data=d, name=iname, case_tube_idx=str(cti), order=i)
            if peak_detector == 'local_max':
                peaks.local_max()
            elif peak_detector == 'cwt':
                peaks.find_peaks_cwt()
                if trim_peaks:
                    peaks.trim_peaks()
            else:
                raise ValueError('peak_detector {} is not valid'.format(peak_detector))

            all_peaks.append(peaks)

        # Find multisample peaks
        # all_peaks.find_peaks()
        # all_peaks.group_peaks.plot(name="{}_all".format(name))

        # Select number of peaks to follow
        if 'npeaks' in kwargs and kwargs['npeaks'] is not None:
            all_peaks.n_group_peaks(kwargs['npeaks'])
        else:
            all_peaks.n_group_peaks()
        log.info("Selecting {} main peaks".format(all_peaks.n_peaks))

        # Label peaks
        peaks_df = all_peaks.label_peaks()

        # Print individual data
        all_peaks.plot_individual()

        return peaks_df

    def get_beads(self, **kwargs):

        # hot fix
        if kwargs['fluorophores'] == ['PE-CF594']:
            kwargs['fluorophores'] = ['PE-TR']

        if kwargs['fluorophores'] == ['APC-H7']:
            kwargs['fluorophores'] = ['APC-CY7']

        if kwargs['fluorophores'] == ['APC-A700']:
            kwargs['fluorophores'] = ['A700']

        if kwargs['fluorophores'] == ['V450']:
            kwargs['fluorophores'] = ['PB']

        if kwargs['fluorophores'] == ['PE-CY55'] or kwargs['fluorophores'] == ['PE-CY5']:
            kwargs['fluorophores'] = ['PERCP-CY55']

        df = self.get_beads_8peak(smooth=False, **kwargs)
        df.set_index(['cytnum', 'date', 'Fluorophore', 'peak'], inplace=True)

        df_ultra = self.get_beads_ultra(smooth=False, **kwargs)
        df_ultra['peak'] = 'ultra'
        df_ultra.set_index(['cytnum', 'date', 'Fluorophore', 'peak'], inplace=True)

        df = pd.concat([df, df_ultra],
                       ignore_index=False)
        df.reset_index(inplace=True, drop=False)
        df.loc[:, 'SD'] = df.MFI.values * df.CV.values/100
        return df

    def plot_beads(self, name='test',
                   **kwargs):
        """ Display bead data """

        df = self.get_beads(**kwargs)

        dfg = df.groupby(['Fluorophore', 'cytnum'])[['date', 'peak', 'MFI', 'SD']]
        for g, beads_df in dfg:

            a = beads_df.groupby(['date', 'peak']).mean()
            a.reset_index(inplace=True, drop=False)

            # Setup colors
            npeaks = len(a.peak.unique())
            colors = brewer2mpl.get_map('Set1', 'Qualitative',
                                        max(npeaks, 3)).hex_colors[::-1]

            # Setup plot
            obs = len(a.date.unique())
            fsize = (max(ceil(obs/4000), 12.5*3),
                     max(ceil(obs/20000), 5*3))
            plt.figure(figsize=fsize)
            ax1 = plt.subplot2grid((4, 1), (0, 0), rowspan=3)

            i = 0
            for g2, dat in a.groupby(['peak']):
                if g2 != 'ultra':
                    plt.plot(dat.date, dat.MFI,
                             c=colors[i], lw=2)
                    ax1.axhline(y=dat.MFI[np.argmin(dat.date)], linewidth=1, linestyle='--',
                                c=colors[i])
                i += 1
            for x in ax1.spines.itervalues():
                x.set_linewidth(1.5)
            ax1.tick_params(axis='both', width=3, length=5, pad=8, direction='out', bottom='off')
            for label in (ax1.get_xticklabels() + ax1.get_yticklabels()):
                label.set_fontsize(24)
                label.set_weight('bold')
            ax1.xaxis.set_ticklabels([])

            ax2 = plt.subplot2grid((4, 1), (3, 0))
            dat = a.loc[a.peak == 'ultra', :]
            plt.plot(dat.date, dat.MFI, c='blue', lw=2)
            ax2.axhline(y=dat.MFI[np.argmin(dat.date)], linewidth=1, linestyle='--',
                        c='blue')
            plt.errorbar(dat.date, dat.MFI, yerr=dat.SD,
                         ecolor='blue', fmt='none')
            ax2.tick_params(axis='both', width=3, length=5, pad=8, direction='out',
                            top='off')
            for x in ax2.spines.itervalues():
                x.set_linewidth(1.5)
            ax2.yaxis.set_major_locator(plt.MaxNLocator(4))
            for label in (ax2.get_xticklabels() + ax2.get_yticklabels()):
                label.set_weight('bold')
                label.set_fontsize(24)

            plt.tight_layout(h_pad=1)
            plt.savefig('.'.join([name, '.'.join(g), 'png']),
                        dpi=200)
            plt.close()

    def histos2tile(self, df, peaks_df=None, beads_df=None, name='test', **kwargs):
        """ Pull 1D histograms (PmtHistos) for a single channel/antigen/..., find peaks, and plot
        """

        df.sort(['date', 'case_tube_idx', 'bin'], inplace=True)
        log.debug("Size of df: {}".format(df.shape))

        # Make n order list
        counts = df.case_tube_idx.value_counts().sort_index(1)
        if len(set(counts)) != 1:
            print counts
            raise ValueError('Not all orders have same count!!')
        df['order'] = np.repeat(range(counts.shape[0]), counts.iloc[0])

        # Figure out X-axis
        dates = [dt.year for dt in df.date.astype(object)]
        if len(set(dates)) <= 2:
            dates = ["{}-{:0>2d}".format(dt.year, dt.month)
                     for dt in df.date.astype(object)]
        if len(set(dates)) <= 1:
            dates = ["{}-{:0>2d}-{:0>2d}".format(dt.year, dt.month, dt.day)
                     for dt in df.date.astype(object)]
        dates = np.asarray(dates)
        date_changes = np.where(dates[range(len(dates)-1)] !=
                                dates[range(1, len(dates))])[0] + 1
        date_changes = [0] + date_changes.tolist()

        # Truncate density so that top outliers don't overload
        max_density = np.percentile(df.density, 99.99)
        df.loc[df.density >= max_density, 'density'] = max_density

        # Make array
        dat = np.asarray(df.density,
                         dtype='float')
        dat.shape = (len(df.order.unique()), counts.iloc[0])
        dat = dat.T

        # Make peaks data
        if peaks_df is not None:
            df.case_tube_idx = df.case_tube_idx.astype(str)
            tmp = df.loc[:, ['case_tube_idx', 'order']].drop_duplicates()
            tmp.set_index(['case_tube_idx'], inplace=True)
            peaks_df = pd.merge(tmp, peaks_df,
                                how='right',
                                left_index=True, right_index=True)
            peaks_df.set_index(['order'], inplace=True)
            peaks_df.sort_index(axis=0, inplace=True)

            name += ".peaks"

        if beads_df is not None:
            tmp = df.loc[:, ['order', 'date']].drop_duplicates()
            tmp.date = pd.DatetimeIndex(tmp.date).date.astype(str)

            beads_df.date = pd.DatetimeIndex(beads_df.date).date.astype(str)

            beads_df = pd.merge(beads_df, tmp, how='right',
                                left_on='date', right_on='date')
            beads_df.drop(['cytnum', 'Fluorophore', 'date', 'CV'], axis=1, inplace=True)
            beads_df = beads_df.groupby(['order', 'peak']).mean()

            name += ".beads"

        # Plot
        fsize = (max(ceil(df.shape[0]/4000), 12*3),
                 max(ceil(df.shape[0]/8000), 6*3))
        plt.figure(figsize=fsize)
        ax = plt.subplot(111)
        plt.imshow(dat, origin='lower', aspect=df.shape[0]/20000)
        ax.set_ylim(0, 100)
        plt.xticks(df.order[date_changes], dates[date_changes], fontweight='bold')

        ax.tick_params(axis='both', width=7, length=9, pad=10, direction='out')
        for label in (ax.get_xticklabels() + ax.get_yticklabels()):
            label.set_fontsize(40)
            label.set_weight('bold')

        if peaks_df is not None:
            colors = brewer2mpl.get_map('YlOrRd', 'Sequential',
                                        max(peaks_df.shape[1], 3)).hex_colors[::-1]
            for i, col in enumerate(peaks_df):
                plt.plot(peaks_df.index, peaks_df[col],
                         linestyle='-', color=colors[i], linewidth=1.5,
                         scalex=False, scaley=False)

        if beads_df is not None:
            dat = beads_df.xs('ultra', level='peak')
            plt.plot(dat.index, dat.MFI + dat.SD, c='orange', lw=4,
                     scalex=False, scaley=False)
            plt.plot(dat.index, dat.MFI, c='red', lw=6,
                     scalex=False, scaley=False)
            plt.plot(dat.index, dat.MFI - dat.SD, c='orange', lw=4,
                     scalex=False, scaley=False)
            ax.axhline(y=dat.MFI.values[0], linewidth=4, linestyle='--',
                       c='red')
            dat = beads_df.xs('P2', level='peak')
            plt.plot(dat.index, dat.MFI, c='green', lw=6,
                     scalex=False, scaley=False)
            ax.axhline(y=dat.MFI.values[0], linewidth=4, linestyle='--',
                       c='green')

        plt.savefig(name + '.png', bbox_inches='tight', dpi=200)
        plt.close()
