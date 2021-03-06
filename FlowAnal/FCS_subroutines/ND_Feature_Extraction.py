# -*- coding: utf-8 -*-
"""
Created on Tue 30 Dec 2014 10:29:41 AM PST
This file describes a feature extraction class for N dimensions

@author: David Ng, MD
"""
__author__ = "David Ng, MD"
__copyright__ = "Copyright 2014"
__license__ = "GPL v3"
__version__ = "1.0"
__maintainer__ = "Daniel Herman"
__email__ = "ngdavid@uw.edu"
__status__ = "Production"

"""Installed Packages"""
import pandas as pd
import numpy as np
import scipy as sp
import h5py
"""Built in packages"""
import os.path
import logging

log = logging.getLogger(__name__)

class ND_Feature_Extraction(object):

    def __init__(self,FCS,bins,**kwargs):
        """ Performs N-Dimenstional Feature Extration on FCS.data
        
        This class takes a data FCS object which as been compensated and
        normalized and generates a sparse array indexed on bin_number and
        normalized number of events in that bin.
        
        Accessiable Parameters:
            .type --            <string> containing a short name for this type
                                         of feature extraction
            .bin_description -- <pd.Series> indexed on data.column names and
                                            storing number of bins on that 
                                            channel/column
            .histogram --       <csr_matrix> indexed on bin_number and the 
                                             normalized number of events in 
                                             that bin.
        
        Accessiable Functions:
            .Return_Coordinates -- Returns the bin centroid for a given index
                                   or bin number (I think...)
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
        #bin the data so that coordinates are generated for every data point in FCS.data
        vector_length,coordinates = self._Uniform_Bin_Data(input_data = FCS.data, bin_dict = bin_dict)

        #generate a sparse array of from the given coordinates
        self.histogram = self._coord2sparse_histogram(vector_length,
                                                      coordinates,
                                                      **kwargs).tocsr()

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

    def _Uniform_Bin_Data(self,input_data,bin_dict):
        """
        fits event parameters to an integer 'binned' value
        """
        basis = [1]         #intialize a list of basis values
        for i in bin_dict.values:
            basis.append(i*basis[-1])   # basis values will be generated dependent on previous value
            # ex base-10 basis = [1,10,100,1000]
            # logic and algorithm from Donald Kunth's Art of Computer Programming Vol 1

        vector_length = basis.pop()         # this is the highest coordinate value (max length of array)
        basis = pd.Series(data=basis,index = bin_dict.index.values)
        rounded = input_data.copy()                 # copy input_data since we will soon operate on it.
        for key in bin_dict.index.values:
            rounded[key] = np.floor(rounded[key]*bin_dict[key]) # iterate and round over every column
        output = rounded[bin_dict.index.values].dot(basis) # apply dot product to multiply columns
                                                            # by basis vector (see Kunth)
        log.debug("Vector Length: {}, \nRounded: {}, \nBasis: {}, \
                   \nCoordinates: {}".format(vector_length,rounded,basis,output))
        if len(input_data) == 0:
            raise ValueError("FCS data is empty!")
        if len(output) == 0:
            raise ValueError("Coordinate Data is empty!")      
        return vector_length, output.apply(np.int64)

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
        if isinstance(index,int):
            index = [index] # make sure index is a list

        coords = self.histogram.indices[index]
        self.x = np.array(np.unravel_index(coords,list(self.bin_description)),dtype=np.float32).T
        temp = self.x / np.array(self.bin_description)[np.newaxis]

        return pd.DataFrame(temp,index=coords,columns=self.bin_description.index.values)

