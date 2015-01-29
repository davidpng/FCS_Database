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

    def __init__(self, dbcon, testing=False, **kwargs):
        self.db = dbcon

        # Load all QC data
        self.TubeStats = self.__get_query_res('TubeStats', index=['date'],
                                              normalize_time=False,
                                              **kwargs)
        if testing is True:
            self.TubeStats.to_sql('full_TubeStats', con=self.db.engine, if_exists='replace',
                                  index=False)

        # self.PmtStats = self.__get_query_res('PmtStats', index=['date', 'Channel_Number'],
        #                                      normalize_time=False, **kwargs)
        # if testing is True:
        #     self.PmtStats.to_sql('full_PmtStats', con=self.db.engine,
        # if_exists='replace', index=False)

        self.PmtCompCorr = self.__get_query_res('PmtCompCorr', **kwargs)
        if testing is True:
            self.PmtCompCorr.to_sql('full_PmtCompCorr', con=self.db.engine,
                                    if_exists='replace', index=False)

        # self.histos = self.__get_histos(**kwargs)
        # if testing is True:
        #     self.histos.to_sql('full_histos', con=self.db.engine,
        # if_exists='replace', index=False)

    def __get_histos(self, table_format='tall', normalize_time=False, **kwargs):
        """ Return pandas df from db table PmtHistos

        NOTE:
        - Adds NAs to densities not present in database table
        """
        df = self.db.query(getPmtHistos=True, **kwargs).results
        df.set_index('date', drop=False, inplace=True)

        if normalize_time is True:
            df2 = normalize_timeseries(df, **kwargs)
            return df2
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
            return df
        else:
            return df

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
