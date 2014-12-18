class FlowQC(object):
    """ Class to encapsulate QC of flow data

    Keyword arguments:
    db  -- FCS_Database object that contains histos and stats
    """

    def __init__(self, db, **kwargs):
        self.db = db
        self.histos = self.__get_histos(**kwargs)
        self.stats = self.__get_stats()

        # TODO: merge relevant tables together

    def __get_histos(self, table_format='wide'):
        """ Return pandas df from db table PmtHistos

        NOTE:
        - Adds NAs to densities not present in database table
        """
        tmp = self.db.sql2pd('PmtHistos')

        if table_format == 'wide':
            tmp.set_index(['case_tube', 'Channel Name', 'bin'], inplace=True)
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
        elif table_format == 'tall':
            tmp.set_index(['case_tube', 'Channel Name', 'bin'], inplace=True)
            tmp = tmp.unstack()
            tmp = tmp.stack(dropna=False)
        else:
            raise ValueError("table_format value %s is invalid" % table_format)

        return tmp

    def __get_stats(self):
        """ Return pandas df from db table PmtStats """
        try:
            return self.db.sql2pd('PmtStats')
        except:
            raise

    def __get_meta(self):
        """ Need to capture relevant meta information """

