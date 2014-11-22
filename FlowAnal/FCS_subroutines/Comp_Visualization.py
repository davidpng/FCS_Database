# -*- coding: utf-8 -*-
"""
Created on Fri 21 Nov 2014 10:59:16 AM PST 
This will generate an image file containing the antigens which high comp issues

@author: David Ng, MD
"""
import matplotlib as plt
import numpy as np

class Comp_Visualization(object):
    def __init__(self,FCS,filename,filetype):
        self.listmode = FCS.data
        self.filename = filename
        self.filetype = filetype
    def plot_
