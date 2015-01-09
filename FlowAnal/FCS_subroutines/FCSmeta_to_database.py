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
__maintainer__ = "Daniel Herman"
__email__ = "hermands@uw.edu"
__status__ = "Subroutine - prototype"

from os.path import relpath, dirname
import logging
log = logging.getLogger(__name__)


class FCSmeta_to_database(object):
    """ Export the meta information in an FCS object to database

    Keyword arguments:
    FCS -- FCS object to export
    db -- database object to write to
    add_lists -- If true, then Antigens and Fluorophores observed are added \
                 to lists (no constraint on namespace)

    """
    def __init__(self, FCS, db, dir=None, add_lists=False):
        self.FCS = FCS
        self.db = db
        self.meta = self.__make_meta(dir=dir)

        # Transfer data
        if self.FCS.empty is False:
            if add_lists:
                self.push_antigens()
                self.push_fluorophores()
            self.push_TubeTypes()
            self.push_TubeCase(dir=dir)
            self.push_parameters()
        else:  # empty FCS push
            log.info('Pushing empty FCS {}'.format(self.FCS.case_tube))
            self.push_TubeCase(dir=dir)

    def __make_meta(self, dir):
        """ Make meta information and return dict """

        meta_data = {'case_tube': self.FCS.case_tube,
                     'filename': self.FCS.filename,
                     'case_number': self.FCS.case_number,
                     'version': self.FCS.version,
                     'case_tube_idx': self.FCS.case_tube_idx}

        if self.FCS.empty is False:
            meta_data['date'] = self.FCS.date
            meta_data['num_events'] = self.FCS.num_events
            meta_data['cytometer'] = self.FCS.cytometer
            meta_data['cytnum'] = self.FCS.cytnum
            meta_data['flag'] = 'GOOD'
        else:
            meta_data['error_message'] = self.FCS.error_message
            if hasattr(self.FCS, 'flag'):
                meta_data['flag'] = self.FCS.flag
            else:
                meta_data['flag'] = 'empty'

        if self.FCS.filepath != 'Does not exist' and dir is not None:
            meta_data['dirname'] = relpath(dirname(self.FCS.filepath), start=dir)
        else:
            meta_data['dirname'] = 'Does not exist'

        return meta_data

    def push_antigens(self):
        """ Export antigens to DB """
        antigens = self.FCS.parameters.loc['Antigen', :].dropna().unique()
        self.db.add_list(x=list(antigens), table='Antigens')

    def push_fluorophores(self):
        """ Export fluorophores to DB """
        fluorophores = self.FCS.parameters.loc['Fluorophore', :].dropna().unique()
        self.db.add_list(x=list(fluorophores), table='Fluorophores')

    def push_TubeTypes(self):
        """ Capture/add TubeTypeInstance """

        # Capture antigen in FCS object
        antigens = self.FCS.parameters.loc['Antigen', :].dropna().unique()
        antigens.sort()
        antigens_string = ';'.join(antigens)

        s = self.db.Session()
        TubeTypesInstances = self.db.meta.tables['TubeTypesInstances']

        try:    # Assign FCS object tube type based on database listing
            self.meta['tube_type_instance'] = s.query(TubeTypesInstances.c.tube_type_instance).\
                                              filter(TubeTypesInstances.c.Antigens == unicode(antigens_string)).one()[0]

        except:  # If tube type is not in the database, then add and then assign
            tube_type = {'tube_type': self.FCS.case_tube.split('_')[1],  # Make placeholder tube type
                         'Antigens': antigens_string}
            self.db.add_list(x=[tube_type['tube_type']], table='TubeTypes')
            self.db.add_dict(tube_type, table='TubeTypesInstances')
            self.meta['tube_type_instance'] = s.query(TubeTypesInstances.c.tube_type_instance).\
                                              filter(TubeTypesInstances.c.Antigens == unicode(antigens_string)).one()[0]
        s.close()

    def push_TubeCase(self, dir):
        """ Push tube+case information FCS object to DB """

        # Push case
        self.db.add_list(x=[self.FCS.case_number], table='Cases')

        # Push case+tube meta information
        self.db.add_dict(self.meta, table='TubeCases')

    def push_parameters(self):
        """ Export Pmt+Tube+Case parameters from FCS object to DB """
        d = self.FCS.parameters.T
        d['version'] = self.FCS.version
        d['case_tube_idx'] = self.FCS.case_tube_idx
        self.db.add_df(df=d, table='PmtTubeCases')
