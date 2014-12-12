# -*- coding: utf-8 -*-
"""
Created on Fri 21 Nov 2014 10:59:16 AM PST 
This will generate an image file containing the antigens which high comp issues

@author: David Ng, MD
"""
import matplotlib as plt
import numpy as np

class Comp_Visualization(object):
    schema = {1:}
    def __init__(self,FCS,filename,filetype):
        self.listmode = FCS.data
        self.filename = filename
        self.filetype = filetype
        print self.listmode.iloc[:,(5,6)]
        
    def display_projection(x_lab,y_lab,x_dat,y_dat):
        pass
