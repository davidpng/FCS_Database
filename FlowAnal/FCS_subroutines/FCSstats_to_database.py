# -*- coding: utf-8 -*-
"""
Created on Fri Oct 24 15:03:23 2014
Provides method to export FCS metadata to DB
@author: hermands
"""

__author__ = "Daniel Herman, MD"
__copyright__ = "Copyright 2014"
__license__ = "GPL v3"
__version__ = "1.0"
__maintainer__ = "David Ng"
__email__ = "hermands@uw.edu"
__status__ = "Subroutine - prototype"

import pandas as pd
import logging
log = logging.getLogger(__name__)


class FCSstats_to_database(object):
    """ Export the stats/histo data in an FCS object to database

    NOTE:
    - If stats or histos do no exist, then nothing to do

    Keyword arguments:
    FCS -- FCS object to export
    db -- database object to write to
    """
    def __init__(self, FCS, db):
        self.FCS = FCS
        self.db = db

        if hasattr(self.FCS, 'PmtStats') and hasattr(self.FCS, 'TubeStats'):
            self.__push_stats()
        else:
            raise "Missing stats"

        if hasattr(self.FCS, 'histos'):
            self.__push_histos()
        else:
            raise "Missing histos"

        if hasattr(self.FCS, 'comp_correlation'):
            self.__push_comp_corr()
        else:
            raise "Missing compensation correlation"

    def __push_stats(self):
        """ Export Pmt event stats and Tube event stats """

        params = self.FCS.parameters.T

        # Handle PmtStats
        d = self.FCS.PmtStats
        d.reset_index(drop=False, inplace=True, col_level=0)
        d.columns.values[0] = "Channel_Name"
        d['version'] = self.FCS.version
        d['case_tube_idx'] = self.FCS.case_tube_idx
        d = pd.merge(d, params[['Channel_Name', 'Channel_Number']],
                     how='left', on=['Channel_Name'])
        d.drop(['Channel_Name'], axis=1, inplace=True)

        mis = [i for i, x in enumerate(d.columns) if x[-1] == '%']
        d.columns = d.columns[range(min(mis))].tolist() + ['X25', 'median', 'X75'] + \
                    d.columns[range(max(mis) + 1, len(d.columns))].tolist()
        self.db.add_df(df=d, table='PmtStats')

        d = self.FCS.TubeStats
        d['version'] = self.FCS.version
        d['case_tube_idx'] = self.FCS.case_tube_idx
        d = pd.Series(d, name='val')
        d = d.reset_index(drop=False).T
        d.columns = d.loc['index', :]
        d.drop(['index'], inplace=True)
#        d.reset_index(inplace=True, drop=True)

        self.db.add_df(df=d, table='TubeStats')

    def __push_histos(self):
        """ Export Pmt event histos
        """
        d = self.FCS.histos.T
        d.reset_index(drop=False, inplace=True, col_level=0)
        d.columns.values[0] = "Channel_Name"
        d['case_tube_idx'] = self.FCS.case_tube_idx

        params = self.FCS.parameters.T
        d = pd.merge(d, params[['Channel_Name', 'Channel_Number']],
                     how='left', on=['Channel_Name'])
        d.drop(['Channel_Name'], axis=1, inplace=True)

        # Pivot table (drop NAs and density of 0)
        d.set_index(["case_tube_idx", "Channel_Number"],
                    drop=True, append=False, inplace=True)
        d2 = d.stack(dropna=False)
        d3 = d2.reset_index(drop=False)
        d3.sort(['case_tube_idx', 'Channel_Number'], inplace=True)
        d3.columns = ['case_tube_idx', 'Channel_Number', 'bin', 'density']

        # Push histo
        self.db.add_df(df=d3, table='PmtHistos')

    def __push_comp_corr(self):
        """ Export compensation correlation data
        """

        d = self.FCS.comp_correlation
        params = self.FCS.parameters.T

        d = pd.merge(d, params[['Channel_Name', 'Channel_Number']],
                     how='left', left_on=['spill_in'], right_on=['Channel_Name'])
        d.drop(['spill_in', 'Channel_Name'], axis=1, inplace=True)
        d.columns = d.columns[range(d.shape[1] - 1)].tolist() + ['Channel_Number_IN']

        d = pd.merge(d, params[['Channel_Name', 'Channel_Number']],
                     how='left', left_on=['spill_from'], right_on=['Channel_Name'])
        d.drop(['spill_from', 'Channel_Name'], axis=1, inplace=True)
        d.columns = d.columns[range(d.shape[1] - 1)].tolist() + ['Channel_Number_FROM']

        d['case_tube_idx'] = self.FCS.case_tube_idx
        self.db.add_df(df=d, table='PmtCompCorr')
