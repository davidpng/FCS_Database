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


class FCSmeta_to_database(object):
    """
    This class includes methods to export FCS meta data to DB
    """
    def __init__(self, FCS, db, dir=None, add_lists=False):
        self.FCS = FCS
        self.db = db

        # Transfer data
        if add_lists:
            self.push_antigens()
            self.push_fluorophores()
        self.push_TubeCase(dir=dir)
        self.push_parameters()

    def push_parameters(self):
        """ Export Pmt+Tube+Case parameters from FCS object to DB """
        d = self.FCS.parameters.T
        d['version'] = self.FCS.version
        d['case_tube'] = self.FCS.case_tube
        self.db.add_df(df=d, table='PmtTubeCases')

    def push_antigens(self):
        """ Export antigens to DB """
        antigens = self.FCS.parameters.loc['Antigen', :].unique()
        self.db.add_list(x=list(antigens), table='Antigens')

    def push_fluorophores(self):
        """ Export fluorophores to DB """
        fluorophores = self.FCS.parameters.loc['Fluorophore', :].unique()
        self.db.add_list(x=list(fluorophores), table='Fluorophores')

    def push_TubeCase(self, dir):
        """ Push tube+case information FCS object to DB """
        meta_data = {'case_tube': self.FCS.case_tube,
                     'filename': self.FCS.filename,
                     'case_number': self.FCS.case_number,
                     'date': self.FCS.date,
                     'num_events': self.FCS.num_events,
                     'cytometer': self.FCS.cytometer,
                     'cytnum': self.FCS.cytnum,
                     'version': self.FCS.version}
        meta_data['dirname'] = relpath(dirname(self.FCS.filepath), start=dir)

        # Push case+tube meta information
        self.db.add_dict(meta_data, table='TubeCases')

        # Push case
        self.db.add_list(x=[self.FCS.case_number], table='Cases')

