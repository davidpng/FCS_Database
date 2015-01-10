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
__status__ = "Production"

from scipy.sparse import csr_matrix
from HDF5_subroutines.HDF5_IO import HDF5_IO

import numpy as np
import pandas as pd
import h5py
import os
import logging
log = logging.getLogger(__name__)


class MergedData_IO(HDF5_IO):
    def __init__(self, filepath, clobber=False):
        """ HDF5 input/output inferface 
        
        This class provides an inferface for taking data from an HDF5 object
        to an dense 'feature' dataframe for input to Machine Learning Algorithms
        
        Keyword Arguements:
        filepath -- <str> Absolute filepath to an HDF5 file for reading and 
                          writing
        clobber -- <bool> Flag to overwrite a HDF5 file object
        
        
        """
        HDF5_IO.__init__(self, filepath, clobber=False)
        print self.filepath
        #self.filepath = filepath
        if clobber is True and os.path.exists(filepath):
            os.remove(filepath)


    def make_single_tube_analysis(self, case_tube_list):
        """
        This function will call a series of case_tube_idx as listed and merge
        into a dense array that is the union of sparse matrix columns
        """
        fh = h5py.File(self.filepath, 'a')

        # error checking
        not_in_data = set([str(x) for x in case_tube_list]) - set(fh['data'].keys())
        if not_in_data:
            raise IOError("Some of the listed case_tubes are not in the \
                           dataset: {}".format(not_in_data))
        # get union of indices
        index_union = self.__get_check_merge_indices(case_tube_list)
        # intialize bin number dataframe AND merge dataframe
        bin_num_df = pd.DataFrame(index_union,columns=['bin_num'])
        merged = bin_num_df
        self.failed_cti = []
        for case in case_tube_list:
            #load FCS Feature Dataframe
            try:
                FCS_ft_df = self.__translate_FCS_feature(case)
                # do a relation algebra join on the bin_number on the union of bin 
                # numbers and index/bin_number of the FCS_features
                merged = pd.merge(merged,FCS_ft_df,how='left',
                                  left_on='bin_num',right_index=True)
             except:
                self.failed_cti.append(case)
        merged.fillna(0,inplace=True) # clear out nan to zero             
        return merged

       
        
    def __push_DataFrame(self, DF, path):
        """
        Method for pushing a full pandas dataframe to the hdf5 file
        """
        fh = h5py.File(self.filepath, 'a')
                
        fh[os.path.joint(path,'index')] = [str(i) for i in DF.index]
        fh[os.path.joint(path,'columns')] = [str(i) for i in DF.columns]
        fh[os.path.joint(path,'data')] = DF.data.astype(str)
        fh.close()
          
    def __pull_DataFrame(self, path):
        """
        Method for returning a full pandas dataframe from teh files       
        """
        fh = h5py.File(self.filepath, 'r')
        DF = pd.DataFrame(data = fh[os.path.joint(path,'data')].value,
                          index = fh[os.path.joint(path,'index')].value,
                          columns = fh[os.path.joint(path,'columns')].value)
        fh.close()
        return DF
        
    def __make_schema(self, case_tube_idx):
        """
        makes a dictionary containing the storage schema
        """
        schema = {"Annotation_DF": "/annotations/",
                  "Feature_DF" : "/features/",
                  "CasesNotFound" : "/not_found"}
        return schema
