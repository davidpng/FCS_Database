# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 18:34:54 2014


@author: David Ng, MD
"""
"""Installed Packages"""
import numpy as np
import pandas as pd
"""Built in packages"""
from re import compile, findall
from datetime import datetime
from warnings import warn
from struct import calcsize, unpack
from os.path import basename, relpath, dirname

from FCS_subroutines.loadFCS import loadFCS
from FCS_subroutines.Process_FCS_Data import Process_FCS_Data
from FCS_subroutines.empty_FCS import empty_FCS
from FCS_subroutines.FCSmeta_to_database import FCSmeta_to_database

class FCS(object):
    """
    This class represents FCS data (Tube+Case information)
    See loadFCS for attribute details
    """
    def __init__(self, version="Blank", filepath=None, db=None, **kwargs):
        self.__version = version
        self.__filepath = filepath
        if isinstantce(filepath,list):
            raise "Not implemneted yet"
            self.make_inferred_FCS(filepaths=filepath)
        if filepath is not None and db is not None:
            raise "Must import data from file or db, not both!"
        elif filepath is not None:
            self.load_from_file(**kwargs)
        elif db is not None:
            self.load_from_db(db)
        
    def load_from_file(self, **kwargs):
        """ 
        Import FCS data from file at <filepath>
        nota bene: import_dataframe needs to be explicitly defined for
        data to be loaded into FCS object        
        """
        loadFCS(FCS=self, filepath=self.__filepath, version=self.__version, **kwargs)

    def load_from_db(self, db):
        """ Import FCS data from db <db> """
        raise "Not implemented"

    def meta_to_db(self, db, dir=None, add_lists=False):
        """ Export meta data from FCS object to db """
        FCSmeta_to_database(FCS=self, db=db, dir=dir, add_lists=add_lists)

    def comp_scale_FCS_data(self,compensation_file,
                            saturation_upper_range=1000,
                            rescale_lim=(-0.15, 1), 
                            limits=False, 
                            strict=True, 
                            **kwargs):
        """calls Process_FCS_Data on self (i.e. an FCS object)"""
        Process_FCS_Data(FCS = self, compensation_file = compensation_file, 
                         saturation_upper_range = saturation_upper_range,
                         rescale_lim = rescale_lim,
                         limits = limits,
                         strict = strict,
                         **kwargs)
                         
    def make_inferred_FCS(self, filepaths):
        """
        filepaths (list)
        """
        pass
                
        
    def emptyFCS(self,dirpath,filepath=None):
        if filepath is not None:
            pass #if filepath is defined in this method's initilization, then use it
        elif filepath is None and self.__filepath is not None:
            filepath = self.__filepath
        elif filepath is None and self.__filepath is None:
            raise "Filepath is not defined in FCS initilization or emptyFCS method"
        else:
            raise "Something is wrong, this case should not occur"
            # this case is included just to make sure no exceptions occur
        
        return empty_FCS(filepath, dirpath, version=self.__version)
if __name__ == '__main__':
    filename = "/home/ngdavid/Desktop/PYTHON/FCS_File_Database/FCS_Database/data/12-00031_Myeloid 1.fcs"

    cwd = os.path.dirname(__file__)
    parent =  os.path.realpath('..')
    root = os.path.realpath('..')
    sys.path.insert(0,parent)
    coords={'singlet': [ (0.01,0.06), (0.60,0.75), (0.93,0.977), (0.988,0.86),
                         (0.456,0.379),(0.05,0.0),(0.0,0.0)],
            'viable': [ (0.358,0.174), (0.609,0.241), (0.822,0.132), (0.989,0.298),
                        (1.0,1.0),(0.5,1.0),(0.358,0.174)]}
    
    comp_file={'H0152':root+'/FCS_Database/data/Spectral_Overlap_Lib_LSRA.txt',
               '2':root+'/FCS_Database/data/Spectral_Overlap_Lib_LSRB.txt'}
    temp = FCS(filepath=filename)
    temp.load_from_file(import_dataframe=True)
        
    temp.comp_scale_FCS_data(comp_file)
    plot(temp.data['SSC-H'],temp.data['CD45 APC-H7'],'b,')