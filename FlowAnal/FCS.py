# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 18:34:54 2014


@author: David Ng, MD
"""
import logging
from FCS_subroutines.loadFCS import loadFCS
from FCS_subroutines.Process_FCS_Data import Process_FCS_Data
from FCS_subroutines.empty_FCS import empty_FCS
from FCS_subroutines.FCSmeta_to_database import FCSmeta_to_database
from . import __version__
import warnings

log = logging.getLogger(__name__)


class FCS(object):
    """
    This class represents FCS data (Tube+Case information)
    See loadFCS for attribute details

    Defining attributes
    .data <pandas dataframe | numpy array> Rows correspond to events, columns to specific Pmt
    .filepath <str> Fullpath of file this represents
    .version <str> Imported from __init__

    Keyword arguments:
    filepath -- fullpath of file to loaded
    filepaths -- list of fullpaths to be loaded for InferenceMatching

    """
    def __init__(self, version=__version__,
                 filepaths=None,
                 filepath=None,
                 db=None,
                 **kwargs):
        self.__version = version
        self.__filepath = filepath

        if filepath is not None:
            try:
                self.load_from_file(**kwargs)
            except Exception, e:
                warnings.warn("loading FCS as empty because %s" % e)
                self.make_emptyFCS(**kwargs)
        elif filepaths is not None:
            raise "Not implemneted yet"
            self.make_inferred_FCS(filepaths=filepaths)
        elif db is not None:
            self.load_from_db(db)
        else:
            log.info("WARNING: did not load any [meta] data")

    def load_from_file(self, **kwargs):
        """ Import FCS data from filepath

        nota bene: import_dataframe needs to be explicitly defined for \
        data to be loaded into FCS object
        """
        loadFCS(FCS=self, filepath=self.__filepath, version=self.__version, **kwargs)

    def make_emptyFCS(self, **kwargs):
        """ Import an "empty" FCS file

        This function handles creation of FCS objects when loadFCS fails
        """
        empty_FCS(FCS=self, filepath=self.__filepath, version=self.__version, **kwargs)

    def load_from_db(self, db):
        """ Import FCS data from db <db> """
        raise "Not implemented"

    def meta_to_db(self, db, dir=None, add_lists=False):
        """ Export meta data from FCS object to db

        Keyword arguments:
        dir -- Directory underwhich all loaded files resides (enables formulation of \
        file relative path)
        add_lists -- If true then all keywords (Antigens, Fluorophores) are automatically loaded \
        into the database. If false and database is in strict mode then will require specific \
        names
        """
        FCSmeta_to_database(FCS=self, db=db, dir=dir, add_lists=add_lists)

    def comp_scale_FCS_data(self, compensation_file,
                            saturation_upper_range=1000,
                            rescale_lim=(-0.15, 1),
                            strict=True,
                            **kwargs):
        """ Updates self.data via call of Process_FCS_Data """
        Process_FCS_Data(FCS=self, compensation_file=compensation_file,
                         saturation_upper_range=saturation_upper_range,
                         rescale_lim=rescale_lim,
                         strict=strict,
                         **kwargs)

    def make_inferred_FCS(self, filepaths):
        """
        filepaths (list)
        """
        raise "Not implemented"


if __name__ == '__main__':
    import os
    import sys
    filename = "/home/ngdavid/Desktop/PYTHON/FCS_File_Database/FlowAnal/data/12-00031_Myeloid 1.fcs"

    cwd = os.path.dirname(__file__)
    parent =  os.path.realpath('..')
    root = os.path.realpath('..')
    sys.path.insert(0,parent)
    coords={'singlet': [ (0.01,0.06), (0.60,0.75), (0.93,0.977), (0.988,0.86),
                         (0.456,0.379),(0.05,0.0),(0.0,0.0)],
            'viable': [ (0.358,0.174), (0.609,0.241), (0.822,0.132), (0.989,0.298),
                        (1.0,1.0),(0.5,1.0),(0.358,0.174)]}

    comp_file={'H0152':root+'/FlowAnal/data/Spectral_Overlap_Lib_LSRA.txt',
               '2':root+'/FlowAnal/data/Spectral_Overlap_Lib_LSRB.txt'}
    temp = FCS(filepath=filename)
    temp.load_from_file(import_dataframe=True)

    temp.comp_scale_FCS_data(comp_file)
    plot(temp.data['SSC-H'],temp.data['CD45 APC-H7'],'b,')
