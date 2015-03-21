# -*- coding: utf-8 -*-
"""
Created on Wed 31 Dec 2014 05:54:41 AM PST
This file describes a HDF5 interface class for pushing and pulling 'binned' histograms
to an HDF5 file format
Contains methods:
push_all, get_all
push_features, get_features
push_not_found, get_not_found
push_annotations, get_annotations

@author: David Ng, MD
"""
__author__ = "David Ng, MD"
__copyright__ = "Copyright 2014"
__license__ = "GPL v3"
__version__ = "1.0"
__maintainer__ = "David Ng"
__email__ = "ngdavid@uw.edu"
__status__ = "Production"

from HDF5_subroutines.HDF5_IO import HDF5_IO

import h5py
import os
import logging
import sys
log = logging.getLogger(__name__)


class MergedFeatures_IO(HDF5_IO):
    def __init__(self, filepath, clobber=False):
        """ HDF5 input/output inferface for the MergedFeatures/ML Input

        This class provides an inferface for taking data from an HDF5 object
        to an dense 'feature' dataframe for input to Machine Learning Algorithms

        Keyword Arguements:
        filepath -- <str> Absolute filepath to an HDF5 file for reading and
                          writing
        clobber -- <bool> Flag to overwrite a HDF5 file object


        """
        super(MergedFeatures_IO, self).__init__(filepath=filepath, clobber=clobber)

    def push_all(self, feat_DF, anno_DF, fail_DF, feat_HDF):
        """wrapper for a bunch of functions"""
        self.push_features(feat_DF)
        self.push_annotations(anno_DF)
        self.push_not_found(fail_DF)
        self.push_meta_data(feat_HDF)

    def get_all(self):
        """wrapper that returns features, annotations and failures"""
        a = self.get_features()
        b = self.get_annotations()
        c = self.get_not_found()
        return a, b, c

    def push_not_found(self, not_found_dic):
        """pushed not found list to the HDF5 """
        schema = self.__make_schema()
        fh = h5py.File(self.filepath, 'a')

        for key, value in not_found_dic.iteritems():
            path = os.path.join(schema['Not_Found'], key)
            try:
                fh[path] = value
            except:
                print sys.exc_info()[0]

        log.debug("Succesfully pushed CaseNotFound dictionary to ML_input hdf5")
        fh.close()

    def get_not_found(self):
        """get not found list from the HDF5 """
        schema = self.__make_schema()
        fh = h5py.File(self.filepath, 'r')
        paths = [str(i) for i in fh[schema['Not_Found']].keys()]
        output = {}
        for p in paths:
            output[p] = fh[os.path.join(schema['Not_Found'], p)]
        return output

    def push_annotations(self, annotation_DF):
        """
        This will push the annotation dataframe
        """
        schema = self.__make_schema()
        self.push_DataFrame(DF=annotation_DF,
                            path=schema['Annotation_DF'])
        log.debug("Succesfully pushed annotation dataframe to ML_input hdf5")

    def get_annotations(self):
        """
        This will get the annotation dataframe
        """
        self.__check_file_schema()
        schema = self.__make_schema()
        DF = self.pull_DataFrame(path=schema['Annotation_DF'])
        log.debug("Succesfully retrived annotation dataframe: {}".format(DF.head()))
        return DF

    def push_features(self, Feature_DF):
        """
        This will push the annotation dataframe
        """
        schema = self.__make_schema()
        self.push_DataFrame(DF=Feature_DF,
                            path=schema['Feature_DF'])
        log.debug("Succesfully pushed Feature dataframe to ML_input hdf5")

    def get_features(self):
        """
        This will push the annotation dataframe
        """
        self.__check_file_schema()
        schema = self.__make_schema()
        DF = self.pull_DataFrame(path=schema['Feature_DF'], dtype=float)
        log.debug("Succesfully retrived feature dataframe: {}".format(DF.head()))
        return DF

    def __check_file_schema(self):
        """
        This checks to make sure the base schema of the input HDF5 file matches
        the given schema
        """
        schema = self.__make_schema()
        schema_check_fail = False
        fh = h5py.File(self.filepath, 'r')

        for key, value in schema.iteritems():
            try:
                temp = fh[value]
            except:
                log.debug("{} does not exist in the hdf5 file at {}".format(value,
                                                                            self.filepath))
                schema_check_fail = True

        if schema_check_fail:
            raise IOError("Input file schema does not match")

    def push_meta_data(self, FTIO_obj):

        self.schema = self.__make_schema()
        fh = h5py.File(self.filepath, 'a')

        FTIO_meta = FTIO_obj.get_meta_data()
        fh[self.schema['database_filepath']] = FTIO_meta['database_filepath']
        fh[self.schema['database_datetime']] = FTIO_meta['database_datetime']
        fh[self.schema['feature_filepath']] = FTIO_obj.filepath
        fh[self.schema['enviroment_version']] = FTIO_meta['enviroment_version']
        fh[self.schema['extraction_type']] = FTIO_meta['extraction_type']
        self.push_Series(SR=FTIO_meta['bin_description'],
                         path=self.schema['bin_description'],
                         ext_filehandle=fh)
        self.push_Series(SR=FTIO_meta['feature_descriptions'],
                         path=self.schema['feature_descriptions'],
                         ext_filehandle=fh)

    def __make_schema(self):
        """
        makes a dictionary containing the storage schema
        """
        schema = {"Annotation_DF": "/annotations/",
                  "Feature_DF": "/features/",
                  "Not_Found": "/missing_because/",
                  "database_filepath": "/database_version/filepath",
                  "database_datetime": "/database_version/date",
                  "enviroment_version": "/enviroment_version",
                  "bin_description": "/bin_description/",
                  "extraction_type": "/extraction_type",
                  "feature_filepath": "/Feature_HDF5/filepath/",
                  "feature_descriptions": "/feature_descriptions/"}
        return schema
