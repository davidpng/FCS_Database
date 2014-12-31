# -*- coding: utf-8 -*-
"""
Created on Wed 31 Dec 2014 05:54:41 AM PST 
This file describes a HDF5 interface class for pushing and pulling 'binned' histograms
to an HDF5 file format
@author: David Ng, MD
"""
__author__ = "David Ng, MD"
__copyright__ = "Copyright 2014"
__license__ = "GPL v3"
__version__ = "1.0"
__maintainer__ = "David Ng"
__email__ = "ngdavid@uw.edu"
__status__ = "Subroutine - prototype"

import h5py

class HDF5_Features(object)
    def __init__(self,filepath):
        self.filepath = filepath
        
    def push_fcs_features(self,case_tube_idx,FCS,db):
        """
        """
        schema = self.__make_schema(case_tube_idx)
        fh = h5py.File(self.filepath,'a+')
        self.__push_check_version(hdf_fh=fh, env_ver=FCS.version, db_file=db.db_file)
        fh.close()

    def get_fcs_features(self,case_tube_idx):
        schema = self.__make_schema(case_tube_idx)
        fh = h5py.File(self.filepath,'r')
        fh.close()

    def __push_check_version(self,hdf_fh,env_ver,db_file):
        """
        if exists and equal = good
        if exists not equal = fail
        if not exist, make and equal        
        """
        if "/database_version/filepath" in hdf_fh:
            if hdf_fh["/database_version/filepath"] != db_file:
                raise ValueError('Filepaths do not match')
        else:
            hdf_fh["/database_version/filepath"] = db_file
            
        if "enviroment_version" in hdf_fh:
            if hdf_fh["enviroment_version"] != evn_ver:
                raise ValueError('Evn versions do not match')
        else:
            hdf_fh["enviroment_version"] = env_ver
            
            
    def __make_schema(self,case_tube_idx):
        """
        makes a list containing the storage schema
        """
        schema = ["/database_version/filepath",
                  "/database_version/date",
                  "/enviroment_version",
                  "/data/"+case_tube_idx+"/data",
                  "/data/"+case_tube_idx+"/indices",
                  "/data/"+case_tube_idx+"/indptr",
                  "/data/"+case_tube_idx+"/shape"]
        return schema
