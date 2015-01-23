class FlowQC(object):
    """ Class to encapsulate QC of flow data

    Keyword arguments:
    db  -- FCS_Database object that contains histos and stats
    """

    def __init__(self, dbcon, **kwargs):
        self.db = dbcon

        # Load all QC data
        self.TubeStats = self.__get_query_res('TubeStats', **kwargs)
        self.PmtStats = self.__get_query_res('PmtStats', **kwargs)
        self.PmtCompCorr = self.__get_query_res('PmtCompCorr', **kwargs)
#        self.histos = self.__get_histos(**kwargs)

    def __get_histos(self, table_format='tall', **kwargs):
        """ Return pandas df from db table PmtHistos

        NOTE:
        - Adds NAs to densities not present in database table
        """
        # TODO: need to get case_tube_idx list, figure out how to query a range of case_tube_idx's, and serialize pull and push [if
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

    def __get_query_res(self, goal, **kwargs):
        """ Return pandas df from db table specified by goal """
        kwargs['get' + goal] = True
        df = self.db.query(**kwargs).results
        return df

    def pushQC(self, db):
        """ Push QC tables to a database """

#        self.histos.to_sql('full_histos', con=db.engine, if_exists='replace', index=False)
        self.PmtStats.to_sql('full_PmtStats', con=db.engine, if_exists='replace', index=False)
        self.TubeStats.to_sql('full_TubeStats', con=db.engine, if_exists='replace', index=False)
        self.PmtCompCorr.to_sql('full_PmtCompCorr', con=db.engine,
                                if_exists='replace', index=False)
