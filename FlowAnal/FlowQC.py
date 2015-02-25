import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta


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


class FlowQC(object):
    """ Class to encapsulate QC of flow data

    Keyword arguments:
    db  -- FCS_Database object that contains histos and stats
    """

    def __init__(self, dbcon, outdbcon=None, testing=False, **kwargs):
        self.db = dbcon
        self.outdb = outdbcon

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
