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

        if hasattr(self.FCS, 'stats'):
            self.__push_stats()
        if hasattr(self.FCS, 'histos'):
            self.__push_histos()

    def __push_stats(self):
        """ Export Pmt event stats """
        d = self.FCS.stats.T
        d.reset_index(drop=False, inplace=True, col_level=0)
        d.columns.values[0] = "Channel Name"
        d['version'] = self.FCS.version
        d['case_tube'] = self.FCS.case_tube
        self.db.add_df(df=d, table='PmtStats')

    def __push_histos(self):
        """ Export Pmt event histos
        """
        d = self.FCS.histos.T
        d.reset_index(drop=False, inplace=True, col_level=0)
        d.columns.values[0] = "Channel Name"
        d['case_tube'] = self.FCS.case_tube

        # Pivot table (drop NAs and density of 0)
        d.set_index(["case_tube", "Channel Name"],
                    drop=True, append=False, inplace=True)
        d2 = d.stack(dropna=False)
        d3 = d2.reset_index(drop=False)
        d3.sort(['case_tube', 'Channel Name'], inplace=True)
        d3.columns = ['case_tube', 'Channel Name', 'bin', 'density']

        # Push bins
        bins = [str(x) for x in d3.bin.unique()]
        self.db.add_list(x=bins, table='HistoBins')

        # Push histo
        self.db.add_df(df=d3, table='PmtHistos')
