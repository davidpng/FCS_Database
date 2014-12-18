class FlowQC(object):
    """ Class to encapsulate QC of flow data

    Keyword arguments:
    db  -- FCS_Database object that contains histos and stats
    """

    def __init__(self, dbcon, **kwargs):
        self.db = dbcon

        # Load all QC data
        self.histos = self.__get_histos(**kwargs)
        self.PmtStats = self.__get_PmtStats(**kwargs)
        self.TubeStats = self.__get_TubeStats(**kwargs)

    def __get_histos(self, table_format='tall', **kwargs):
        """ Return pandas df from db table PmtHistos

        NOTE:
        - Adds NAs to densities not present in database table
        """
        tmp = self.db.query(getPmtHistos=True, **kwargs).results
        if table_format == 'wide':
            meta_cols = [c for c in tmp.columns if c not in ['density']]
            tmp.set_index(meta_cols, inplace=True)
            tmp = tmp.unstack()
            tmp.reset_index(drop=False, inplace=True, col_level=0)

            # Fix column names
            new_columns = []
            for i in range(len(tmp.columns)):
                if tmp.columns[i][1] == '':
                    new_columns.append(tmp.columns[i][0])
                else:
                    new_columns.append(tmp.columns[i][1])
            tmp.columns = new_columns

        return tmp

    def __get_PmtStats(self, **kwargs):
        """ Return pandas df from db table PmtStats """

        df = self.db.query(getPmtStats=True, **kwargs).results
        return df

    def __get_TubeStats(self, **kwargs):
        """ Return pandas df from db table PmtStats """

        df = self.db.query(getTubeStats=True, **kwargs).results
        return df

    def pushQC(self, db):
        """ Push QC tables to a database """

        self.histos.to_sql('full_histos', con=db.engine, if_exists='replace', index=False)
        self.PmtStats.to_sql('full_PmtStats', con=db.engine, if_exists='replace', index=False)
        self.TubeStats.to_sql('full_TubeStats', con=db.engine, if_exists='replace', index=False)
