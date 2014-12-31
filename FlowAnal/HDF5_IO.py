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
from scipy.sparse import csr_matrix

class HDF5_IO(object):
    def __init__(self,filepath):
        self.filepath = filepath
        
    def push_fcs_features(self,case_tube_idx,FCS,db):
        """
        """
        self.schema = self.__make_schema(str(case_tube_idx))
        fh = h5py.File(self.filepath,'a')
        self.__push_check_version(hdf_fh=fh, FCS=FCS, db=db)
        #push sparse data into dir named for case_tube_idx
        fh[self.schema['sdat']] = FCS.FCS_features.histogram.data
        fh[self.schema['sidx']] = FCS.FCS_features.histogram.indices
        fh[self.schema['sind']] = FCS.FCS_features.histogram.indptr
        fh[self.schema['sshp']] = FCS.FCS_features.histogram.shape        
        fh.close()
           
    def get_fcs_features(self,case_tube_idx):
        self.schema = self.__make_schema(str(case_tube_idx))
        fh = h5py.File(self.filepath,'r')

        d = fh[self.schema['sdat']].value
        i = fh[self.schema['sidx']].value
        p = fh[self.schema['sind']].value
        s = fh[self.schema['sshp']].value
        
        fh.close()
        return csr_matrix((d,i,p),shape=s)

    def __push_check_version(self,hdf_fh,FCS,db):
        """
        if exists and equal = good
        if exists not equal = fail
        if not exist, make and equal        
        """
        if self.schema['db_fp'] in hdf_fh:
            if hdf_fh[self.schema['db_fp']] != db.db_file:
                raise ValueError('Filepaths do not match')
        else:
            hdf_fh[self.schema['db_fp']] = db.db_file
            
        if self.schema['env_v'] in hdf_fh:
            if hdf_fh[self.schema['env_v']] != FCS.version:
                raise ValueError('Evn versions do not match')
        else:
            hdf_fh[self.schema['env_v']] = FCS.version

        if self.schema['ex_tp'] in hdf_fh:
            if hdf_fh[self.schema['ex_tp']] != FCS.FCS_features.type:
                raise ValueError('Evn versions do not match')
        else:
            hdf_fh[self.schema['ex_tp']] = FCS.FCS_features.type
            
            
    def __make_schema(self,case_tube_idx):
        """
        makes a list containing the storage schema
        """
        schema = {"db_fp": "/database_version/filepath",
                  "db_dt": "/database_version/date",
                  "env_v": "/enviroment_version",
                  "ex_tp": "/extraction_type",
                  "sdat": "/data/"+case_tube_idx+"/data",
                  "sidx": "/data/"+case_tube_idx+"/indices",
                  "sind": "/data/"+case_tube_idx+"/indptr",
                  "sshp": "/data/"+case_tube_idx+"/shape"}
        return schema
