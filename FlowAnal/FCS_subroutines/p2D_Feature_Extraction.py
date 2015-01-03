# -*- coding: utf-8 -*-
"""
Created on Tue 30 Dec 2014 10:29:41 AM PST 
This file describes a feature extraction class for N dimensions

@author: David Ng, MD
"""
import os.path

import pandas as pd
import numpy as np
import scipy as sp

import h5py
import logging
import itertools
log = logging.getLogger(__name__)

class p2D_Feature_Extraction(object):

    def __init__(self,FCS,bins,**kwargs):
        """
        bins = number of bins per axis
        Accessiable Parameters
        type
        bin_description
        histogram
        """
        self.type = 'Full'
        if 'exclude_param' in kwargs:
            exclude = kwargs['exclude_param']
        else:
            exclude = ['FSC-H','SSC-A','Time']
        #generate list of columns to be used
        columns = [c for c in FCS.data.columns if c not in exclude]
        #generate a dictionary describing the bins to be used
        bin_dict = self._Generate_Bin_Dict(columns,bins)
        self.bin_description = bin_dict
        self.histogram = self._flattened_2d_histograms(FCS_data=FCS.data,
                                                       columns=columns,
                                                       bin_dict=bin_dict,**kwargs)
        
    def _flattened_2d_histograms(self,FCS_data,columns,bin_dict,ul=1.0,normalize=True,**kwargs):
        """
        """

        feature_space=[]
        for features in itertools.combinations(columns,2):
            dim = (bin_dict[features[0]],bin_dict[features[1]])
            log.info(features)
            histo2d,xbin,ybin = np.histogram2d(FCS_data[features[0]],
                                               FCS_data[features[1]],
                                               bins=dim,
                                               range=[[0,ul],[0,ul]],
                                               normed=normalize)
            #feature_space.extend(np.ravel(1-1/((histo2d*scaling)**0.75+1)))
            feature_space.extend(np.ravel(histo2d))
        return sp.sparse.csr_matrix(feature_space)
        
    def _coord2sparse_histogram(self,vector_length,coordinates,normalize=True,**kwargs):
        """
        generates a sparse matrix with normalized histogram counts
        each bin describes the fraction of total events within it (i.e. < 1)
        """
        output=sp.sparse.lil_matrix((1,vector_length), dtype=np.float32)
        for i in coordinates:
            output[0,i]+=1
        if normalize:
            return output/ len(coordinates)
        else:
            return output
       
    def _Generate_Bin_Dict(self,columns,bins):
        """
        Performs error checking and type converion for bins
        """
        if isinstance(bins,int):
            bin_dict = pd.Series([bins] * len(columns),index=columns)
        elif isinstance(bins,list):
            if len(bins) != len(columns):
                raise RuntimeWarning("number of bins in the list does not match the number of parameters")
            else:
                bin_dict = pd.Series(bins,columns)
        elif isinstance(bins,dict):
            if bins.keys() not in columns or columns not in bins.keys():
                raise RuntimeWarning("The bin keys do not match the provided columns")
            else:
                raise RuntimeWarning("bin dict not implemented")
        else:
            raise TypeError("provided bins parameter is not supported")
        return bin_dict

    def Return_Coordinates(self,index):
        """
        Returns the bin parameters 
        """
        pass

