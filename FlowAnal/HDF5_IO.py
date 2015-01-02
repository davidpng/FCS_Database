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

import pandas as pd
import h5py
from scipy.sparse import *0
import os
import logging
log = logging.getLogger(__name__)


class HDF5_IO(object):
    def __init__(self, filepath, clobber=False):
        self.filepath = filepath
        if clobber is True and os.path.exists(filepath):
            os.remove(filepath)

    def make_single_tube_analysis(self, case_tube_list):
        """
        This function will call a series of case_tube_idx as listed and merge
        into a dense array that is the union of sparse matrix columns
        """
        fh = h5py.File(self.filepath, 'a')

        # error checking
        not_in_data = set(case_tube_list) - set(fh['data'].keys())
        if not_in_data:
            raise "Some of the listed case_tubes are not in the dataset"
            print not_in_data
        # get union of indices
        index_union = self.__get_check_merge_indices(case_tube_list)
        # intialize bin number dataframe AND merge dataframe
        bin_num_df = pd.DataFrame(index_union,columns=['bin_num'])
        merged = bin_num_df
        
        for case in case_tube_list:
            #load FCS Feature Dataframe
            FCS_ft_df = self.__translate_FCS_feature(case)
            # do a relation algebra join on the bin_number on the union of bin 
            # numbers and index/bin_number of the FCS_features
            merged = pd.merge(merged,FCS_ft_df,how='left',
                              left_on='bin_num',right_index=True)
        merged.fillna(0,inplace=True) # clear out nan to zero             
        return merged
        
    def __translate_FCS_feature(self,case_tube_idx)
        """
        makes a dataframe containing the index and data information of the
        original sparse matrix
        """
        sparse_mtx = get_fcs_features(case_tube_idx)
        return pd.DataFrame(data=sparse_mtx.data,
                            index=sparse_mtx.indices,
                            columns=[str(case_tube_idx)])

        
    def __get_check_merge_indices(self, case_tube_list):
        """
        This will return a list of the union of index positions for all
        listed case_tube
        """

        fh = h5py.File(self.filepath, 'a')
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
            return np.sort(np.unique(np.array(index)))

    def push_fcs_features(self, case_tube_idx, FCS, db):
        """
        This function will push the fcs features stored in CSR matrix form
        to a given case_tube_idx as well as associated meta information
        """
        self.schema = self.__make_schema(str(case_tube_idx))
        fh = h5py.File(self.filepath, 'a')
        self.__push_check_version(hdf_fh=fh, FCS=FCS, db=db)

        # push sparse data into dir named for case_tube_idx
        fh[self.schema['sdat']] = FCS.FCS_features.histogram.data
        fh[self.schema['sidx']] = FCS.FCS_features.histogram.indices
        fh[self.schema['sind']] = FCS.FCS_features.histogram.indptr
        fh[self.schema['sshp']] = FCS.FCS_features.histogram.shape
        fh.close()

    def get_fcs_features(self, case_tube_idx):
        """
        This function will return the CSR matrix for a given case_tube_idx
        """
        self.schema = self.__make_schema(str(case_tube_idx))
        fh = h5py.File(self.filepath, 'r')

        # get individual componets of the sparse array
        d = fh[self.schema['sdat']].value
        i = fh[self.schema['sidx']].value
        p = fh[self.schema['sind']].value
        s = fh[self.schema['sshp']].value

        fh.close()
        return csr_matrix((d,i,p),shape=s)

    def __push_check_version(self, hdf_fh, FCS, db):
        """
        This internal function will check to see the header info the
        hdf5 object/file is correct per the following logic
        if exists and equal = good
        if exists not equal = fail
        if not exist, make and equal

        Items used: FCS.version, FCS.FCS_features.type, db.date, db.db_file
        """
        if self.schema['db_fp'] in hdf_fh:
            if hdf_fh[self.schema['db_fp']].value != db.db_file:
                raise ValueError('Filepaths do not match: %s <==> %s' %
                                 (hdf_fh[self.schema['db_fp']].value,
                                  db.db_file))
        else:
            hdf_fh[self.schema['db_fp']] = db.db_file

        db_creation_date = db.creation_date.strftime("%Y-%m-%d")  # HDF5 does not handle datetime
        if self.schema['db_dt'] in hdf_fh:
            if hdf_fh[self.schema['db_dt']].value != db_creation_date:
                raise ValueError('DB dates do not match')
        else:
            hdf_fh[self.schema['db_dt']] = db_creation_date

        if self.schema['env_v'] in hdf_fh:
            if hdf_fh[self.schema['env_v']].value != FCS.version:
                raise ValueError('Evn versions do not match')
        else:
            hdf_fh[self.schema['env_v']] = FCS.version

        if self.schema['ex_tp'] in hdf_fh:
            if hdf_fh[self.schema['ex_tp']].value != FCS.FCS_features.type:
                raise ValueError('Evn versions do not match')
        else:
            hdf_fh[self.schema['ex_tp']] = FCS.FCS_features.type

        log.debug('Schema: %s' % ', '.join([i + '=' + str(hdf_fh[self.schema[i]].value)
                                            for i in ['ex_tp', 'env_v', 'db_dt', 'db_fp']]))

    def __make_schema(self, case_tube_idx):
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
