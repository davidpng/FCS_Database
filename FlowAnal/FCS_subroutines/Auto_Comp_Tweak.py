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
from Process_FCS_Data import Process_FCS_Data
from itertools import combinations

class Auto_Comp_Tweak(object):
    self.ignore = ['SSC-H','SSC-A','FCS-H','FCS-A','Time']
    Gates={'LR': [ (0.7,-0.2), (1.5,-0.2), (1.5,0.6), (1.0,0.6),
                         (0.7,0.3),(0.7,-0.2)],
           'UL': [ (-0.2,0.7), (-0.2,1.5), (0.6,1.5), (0.6,1.0),
                        (0.3,0.7),(-0.2,0.7)]}
                        
    def __init__(self,Process_FCS_object):
        self.input = Process_FCS_object
        self.data = Process_FCS_object.FCS.data        
        self.antigens = self.__find_antigens(self.input.FCS.parameters)
        #self.input.__gating(data, x_ax, y_ax, coords)
        
    def __find_antigens(self,parameters):
        """
        Find parameters with defined antigens, exclude 'SSC-H','SSC-A','FCS-H','FCS-A','Time'
        
        """
        index = parameters[:]['Antigen'] != 'Unknown'
        antigens = parameters[index]['Channel Name']
        return list(set(antigens)-set(self.ignore))
        
    def __iterate_combos(self):
        """
        Makes a list of all unique pairwise combinations of antigens
        """
        return combinations(self.antigens,2)