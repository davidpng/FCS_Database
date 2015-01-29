# -*- coding: utf-8 -*-
"""
Created on Thu Nov  6 11:49:11 2014
This function provides a heurtistic method for tweaking compensation.
Requires Process_FCS_Data Class
Specifically uses:
Process_FCS_Data.__gating()
Process_FCS_Data.FCS.data
Process_FCS_Data.FCS.parameters
Process_FCS_Data._make_comp_matrix()
Process_FCS_Data.overlap_matrix
@author: ngdavid
"""
#from Process_FCS_Data import Process_FCS_Data
from itertools import combinations
import pandas as pd
from scipy import stats
import numpy as np
class Auto_Comp_Tweak(object):
    ignore = ['SSC-H','SSC-A','FCS-H','FCS-A','Time']
    Gates={'LR': [ (0.7,-0.2), (1.5,-0.2), (1.5,0.6), (1.0,0.6),
                         (0.7,0.3),(0.7,-0.2)],
           'UL': [ (-0.2,0.7), (-0.2,1.5), (0.6,1.5), (0.6,1.0),
                        (0.3,0.7),(-0.2,0.7)]}
                        
    def __init__(self,Process_FCS_object):
        self.Gates={'LR': [ (0.7,-0.2), (1.5,-0.2), (1.5,0.6), (1.0,0.6),
                         (0.7,0.3),(0.7,-0.2)],
                    'UL': [ (-0.2,0.7), (-0.2,1.5), (0.6,1.5), (0.6,1.0),
                         (0.3,0.7),(-0.2,0.7)]}
        self.input = Process_FCS_object
        self.data = self.input._LogicleRescale(self.input.FCS.data, T=2**18, M=4, W=0.5, A=0)
        self.antigens_to_comp = self.__find_antigens(self.input.FCS.parameters)

        self.overlap_matrix = pd.DataFrame(self.input.overlap_matrix,
                                           columns = self.data.columns,
                                           index = self.data.columns)
        
        self.comp_matrix = self.input._make_comp_matrix(self.overlap_matrix)

        #self.print_spectral_correlation(file="/home/davidng/Desktop/PreComp_Corr.txt")

        self.data = self.data.dot(self.input.overlap_matrix)
        self.data.columns = self.input.FCS.data.columns
        #need to reset the column names since dot doesn't carry over

        #self.print_spectral_correlation(file="/home/davidng/Desktop/PostComp_Corr.txt")

        self.data = self.data.values

    def print_spectral_correlation(self,file=None):
        """
        This will display the correlations of the gated populations,
        i.e. the populations with comp issues
        """
        if file:
            fo = open(file,'w+')

        pairlist = [i for i in self.__iterate_combos(self.antigens_to_comp)]
        for pair in pairlist:
            index_mask = self.input._gating(self.data,pair[0],pair[1],self.Gates['LR'])
            slope, intercept, r_value, p_value, std_err = stats.linregress(self.data.loc[index_mask,pair])
            out_str = "Correlation of {} into {}: {} r-val: {}\n".format(pair[0],pair[1],slope,r_value)
            if file:
                fo.write(out_str)
            else:
                print(out_str)
        if file:
            fo.close()

    def print_spectral_overlaps(self,file=None):
        print self.overlap_matrix        
        for pair in self.__iterate_combos(self.antigens_to_comp):
            print("Overlap of {} into {} : {}".format(pair[0],pair[1],
                  self.overlap_matrix.loc[pair[0],pair[1]]))
            print("Overlap of {} into {} : {}".format(pair[1],pair[0],
                  self.overlap_matrix.loc[pair[1],pair[0]]))
            
    def __xy_comp(self,x,y):
        """
        Works on the upper left quadrant
        """
        
    def __find_antigens(self,parameters):
        """
        Find parameters with defined antigens, exclude 'SSC-H','SSC-A','FCS-H','FCS-A','Time'
        
        """
        index = parameters.loc['Antigen',:] != 'Unknown'
        column_names = parameters.loc['Channel Name',index]
        return column_names
        
    def __iterate_combos(self,antigens):
        """
        Makes a list of all unique pairwise combinations of antigens
        """
        return combinations(antigens,2)