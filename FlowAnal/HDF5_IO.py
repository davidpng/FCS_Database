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
    
    
    def make_single_tube_analysis(self,case_tube_list):
        """
        This function will call a series of case_tube_idx as listed and merge 
        into a dense array that is the union of sparse matrix columns
        """
        fh = h5py.File(self.filepath,'a')
        #error checking
        not_in_data = set(case_tube_list) - set(fh['data'].keys()) 
        if not_in_data:
            raise "Some of the listed case_tubes are not in the dataset"
            print not_in_data
            
    def __get_check_merge_indices(self,case_tube_list):
        """
        This will return a list of the union of index positions for all 
        listed case_tube
        """
       
        fh = h5py.File(self.filepath,'a')
        index = []
        shape = []
        for i in case_tube_list:        
            self.schema = self.__make_schema(str(i))
            index.append(fh[self.schema['sidx']].value)
            shape.append(fh[self.schema['sshp']].value)
        fh.close()
        
        #check shape matches
        areTrue = [shape[i]==shape[i-1] for i in range(1,len(shape))]
        if not np.all(areTrue):
            print np.array(shape)
            raise "The lenght/shape of one case does not match the others"
        else:
            return np.unique(np.array(index))    
        
        
    def push_fcs_features(self,case_tube_idx,FCS,db):
        """
        This function will push the fcs features stored in CSR matrix form
        to a given case_tube_idx as well as associated meta information
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
        """
        This function will return the CSR matrix for a given case_tube_idx
        """
        self.schema = self.__make_schema(str(case_tube_idx))
        fh = h5py.File(self.filepath,'r')
        #get individual componets of the sparse array
        d = fh[self.schema['sdat']].value
        i = fh[self.schema['sidx']].value
        p = fh[self.schema['sind']].value
        s = fh[self.schema['sshp']].value
        
        fh.close()
        return csr_matrix((d,i,p),shape=s)

    def __push_check_version(self,hdf_fh,FCS,db):
        """
        This internal function will check to see the header info the 
        hdf5 object/file is correct per the following logic
        if exists and equal = good
        if exists not equal = fail
        if not exist, make and equal
        
        Items used: FCS.version, FCS.FCS_features.type, db.date, db.db_file
        """
        if self.schema['db_fp'] in hdf_fh:
            if hdf_fh[self.schema['db_fp']] != db.db_file:
                raise ValueError('Filepaths do not match')
        else:
            hdf_fh[self.schema['db_fp']] = db.db_file
        """
        if self.schema['db_dt'] in hdf_fh:
            if hdf_fh[self.schema['db_dt']] != db.date
                raise ValueError('Evn versions do not match')
        else:
            hdf_fh[self.schema['db_dt']] = db.date
        """
            
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
