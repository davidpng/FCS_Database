"""
Classes and functions through which database and py HP data interact
"""

import os


class FCSmeta_to_DB(object):
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
        """ Push parameters from FCS object to DB """
        d = self.FCS.parameters.T
        d['case_tube'] = self.FCS.case_tube
        self.db.add_df(df=d, table='PmtTubeCases')

    def push_antigens(self):
        antigens = self.FCS.parameters.loc['Antigen', :].unique()
        self.db.add_list(x=list(antigens), table='Antigens')

    def push_fluorophores(self):
        fluorophores = self.FCS.parameters.loc['Fluorophore', :].unique()
        self.db.add_list(x=list(fluorophores), table='Fluorophores')

    def push_TubeCase(self, dir):
        """ Push case from FCS object to DB """
        meta_data = {'case_tube': self.FCS.case_tube,
                     'filename': self.FCS.filename,
                     'case_number': self.FCS.case_number,
                     'date': self.FCS.date,
                     'num_events': self.FCS.num_events,
                     'cytometer': self.FCS.cytometer,
                     'cytnum': self.FCS.cytnum}
        meta_data['dirname'] = os.path.relpath(os.path.dirname(self.FCS.filepath), start=dir)

        # Push case+tube meta information
        self.db.add_dict(meta_data, table='TubeCases')

        # Push case
        self.db.add_list(x=[self.FCS.case_number], table='Cases')
