# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 18:34:54 2014
This files descrbies the FCS class which contains IO handling for 
FCS type data, post processing, statistics extraction to a database,
meta_info extraction to a database, visualization and Feature Extraction
(i.e. binning) to an HDF5 file

@author: ngdavid
"""
__author__ = "David Ng, MD"
__copyright__ = "Copyright 2014, David Ng"
__license__ = "GPL v3"
__version__ = "1.7"
__maintainer__ = "David Ng"
__email__ = "ngdavid@uw.edu"
__status__ = "Production"

from FCS_subroutines.loadFCS import loadFCS
from FCS_subroutines.Process_FCS_Data import Process_FCS_Data
from FCS_subroutines.empty_FCS import empty_FCS
from FCS_subroutines.FCSmeta_to_database import FCSmeta_to_database
from FCS_subroutines.FCSstats_to_database import FCSstats_to_database
from FCS_subroutines.Extract_HistoStats import Extract_HistoStats
from FCS_subroutines.Comp_Visualization import Comp_Visualization
from FCS_subroutines.ND_Feature_Extraction import ND_Feature_Extraction
from FCS_subroutines.p2D_Feature_Extraction import p2D_Feature_Extraction
from . import __version__

import warnings
import logging
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
                 case_tube_idx=0,
                 **kwargs):
        self.__version = version
        self.__filepath = filepath
        self.__comp_scale_ran = False
        if filepath is not None:
            self.case_tube_idx = case_tube_idx
            try:
                self.load_from_file(**kwargs)
            except Exception, e:
                warnings.warn("loading FCS as empty because %s" % e)
                self.make_emptyFCS(error_message=str(e), **kwargs)
        elif filepaths is not None:
            raise Exception("Not implemneted yet!!!!!!!!!")
            self.make_inferred_FCS(filepaths=filepaths)
        elif db is not None:
            self.load_from_db(db)
        else:
            self.make_emptyFCS(**kwargs)

    def load_from_file(self, **kwargs):
        """ Import FCS data from filepath

        nota bene: import_dataframe needs to be explicitly defined for \
        data to be loaded into FCS object
        """
        loadFCS(FCS=self, filepath=self.__filepath, version=self.__version, **kwargs)

    def make_emptyFCS(self, error_message, **kwargs):
        """ Import an "empty" FCS file

        This function handles creation of FCS objects when loadFCS fails
        """
        empty_FCS(FCS=self, error_message=error_message,
                  filepath=self.__filepath, version=self.__version, **kwargs)

    def load_from_db(self, db):
        """ Import FCS data from db <db> """
        raise "Not implemented"

    def comp_scale_FCS_data(self, compensation_file,
                            saturation_upper_range=1000,
                            rescale_lim=(-0.15, 1),
                            strict=True,
                            auto_comp=False,
                            **kwargs):
        """ Updates self.data via call of Process_FCS_Data
        """
        if not self.__comp_scale_ran:
            Process_FCS_Data(FCS=self, compensation_file=compensation_file,
                             saturation_upper_range=saturation_upper_range,
                             rescale_lim=rescale_lim,
                             strict=strict,
                             auto_comp=auto_comp,
                             **kwargs)
            self.__comp_scale_ran = True
        else:
            raise RuntimeError("Comp_Scale_FCS_Data method has already been run")
            
    def feature_extraction(self, extraction_type='Full', bins=10, **kwargs):
        """
        Quasi interal function to FCS, to be accessed by other functions?
        Will extract features to an sparse data array
        extraction type - flag for 2-D vs N-D binning
        **kwargs - to pass bin size information etc
        """
        type_flag = extraction_type.lower()
        if type_flag == 'full':
            self.FCS_features = ND_Feature_Extraction(FCS=self,
                                                      bins=bins,
                                                      **kwargs)

        elif type_flag == '2d':
            self.FCS_features = p2D_Feature_Extraction(FCS=self,
                                                      bins=bins,
                                                      **kwargs)
        else:
            raise ValueError("Extraction type undefined")

    def Push_FCS_features_to_HDF5(self,case_tube_index, HDF5_object, db_h):
        """
        This will push object described
        """
        if not self.FCS_features:
            raise ValueError("FCS_features does not exist, did you call \
                   _feature_extraction first to make?")

        HDF5_object.push_FCS_features(case_tube_index,FCS=self,db_h=db_h,)

    def make_inferred_FCS(self, filepaths):
        """
        filepaths (list)
        """
        raise "Not implemented"

    def extract_FCS_histostats(self):
        """
        Calls Function to make pandas dataframe of columnwise histograms and statistics
        """
        Extract_HistoStats(FCS=self)

    def comp_visualize_FCS(self, outfile, outfiletype="PNG"):
        """ Makes a pdf file containing the visizliations of the FCS file

        outfile -- output filename

        Optional arguments:
        outfiletype -- accepts PDF, PNG, JPEG (overidden by filename suffix)

        """
        Comp_Visualization(FCS=self, outfile=outfile, outfiletype=outfiletype)

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

    def histostats_to_db(self, db):
        """ Add histostats to db """

        FCSstats_to_database(FCS=self, db=db)

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
