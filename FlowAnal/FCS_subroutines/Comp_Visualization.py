# -*- coding: utf-8 -*-
"""
Created on Fri 21 Nov 2014 10:59:16 AM PST 
This will generate an image file containing the antigens which high comp issues

@author: David Ng, MD
"""
import matplotlib.pyplot as plt
import numpy as np

class Comp_Visualization(object):
    schema = {1: {1:(5,10), 2:(6,10)},
              2: {1:(6,5), 2:(7,5), 3:(8,5), 4:(9,5)},
              3: {1:(7,6), 2:(8,6), 3:(9,6)},
              4: {1:(11,7), 2:(8,7), 3:(9,7)},
              5: {1:(9,8), 2:(13,8)},
              6: {1:(14,9)},
              7: {1:(12,11), 2:(13,11)},
              8: {1:(13,12), 2:(14,12)},
              9: {1:(14,13)} }
    def __init__(self,FCS,filename,filetype):
        self.FCS = FCS
        self.filename = filename
        self.filetype = filetype
        self.plot_2d(1,4)
        
    def plot_2d(self,x,y):
        x_lb=self.FCS.parameters.iloc[:,x-1].loc['Channel Name']
        y_lb=self.FCS.parameters.iloc[:,y-1].loc['Channel Name']
        
        plt.plot(self.FCS.data.iloc[:,x-1],
                 self.FCS.data.iloc[:,y-1],'b,')
        plt.xlabel(x_lb)
        plt.ylabel(y_lb)
        plt.xlim(0,1)
        plt.ylim(0,1)
        plt.savefig(self.filename,bbox_inches='tight')

