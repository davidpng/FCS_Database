# -*- coding: utf-8 -*-
"""
Created on Fri 21 Nov 2014 10:59:16 AM PST 
This will generate an image file containing the antigens which high comp issues

@author: David Ng, MD
"""
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

schema = {1: {1:(5,10), 2:(6,10)},
              2: {1:(6,5), 2:(7,5), 3:(8,5), 4:(9,5)},
              3: {1:(7,6), 2:(8,6), 3:(9,6)},
              4: {1:(11,7), 2:(8,7), 3:(9,7)},
              5: {1:(9,8), 2:(13,8)},
              6: {1:(14,9)},
              7: {1:(12,11), 2:(13,11)},
              8: {1:(13,12), 2:(14,12)},
              9: {1:(14,13)} }

class Comp_Visualization(object):
    
    def __init__(self,FCS,filename,filetype):
        self.FCS = FCS
        self.filename = filename
        self.filetype = filetype
        #print self.FCS.data
        self.display_projection(1,2,3,4)
        
    def display_projection(self,x_lab,y_lab,x_dat,y_dat):
        pass
        self.walk_schema()
        self.setup_plotting()
        
    def setup_plotting(self):
        fig = plt.gcf()
        fig.set_size_inches(12,20)
        fig.tight_layout()
        fig.savefig(self.filename,dpi=500,bbox_inches='tight')

    def walk_schema(self):
        """
        i = rows
        j = columns
        """

        for i,value in schema.iteritems():
            for j,items in value.iteritems():
                plt.subplot2grid((9,4),(i-1,j-1))
                self.plot_2d_hist(items[0],items[1])
                
        plt.subplot2grid((9,4),(8,3))
        self.plot_2d_hist(4,14)
        
    def plot_2d_hist(self,x,y,downsample=0.2):
        x_lb = self.FCS.parameters.iloc[:,x-1].loc['Channel Name']
        y_lb = self.FCS.parameters.iloc[:,y-1].loc['Channel Name']
        
        x_pts = self.FCS.data.iloc[:,x-1]
        y_pts = self.FCS.data.iloc[:,y-1]
        indicies = np.random.choice(x_pts.index,int(downsample*len(x_pts)))
        """ 
        #Legacy Code: Old Patching Routine, moved to Process_FCS_Data
        Remove after viz_dev_06 is merged with master
        if x not in [1,2,3,4]:
            x_pts = 1 - x_pts 
        if y not in [1,2,3,4]:
            y_pts = 1 - y_pts
        """

        plt.plot(x_pts[indicies],y_pts[indicies],'b.',markersize=1,alpha=0.7)
        plt.xlabel(x_lb)
        plt.ylabel(y_lb)
        plt.xlim(0,1)
        plt.ylim(0,1)
        plt.xticks([])
        plt.yticks([])
        
        plt.gca().set_aspect('equal', adjustable='box')

