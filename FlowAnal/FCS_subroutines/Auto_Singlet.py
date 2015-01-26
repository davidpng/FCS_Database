# -*- coding: utf-8 -*-
"""
Created on Sat 24 Jan 2015 05:19:00 AM PST 
Provides Auto Singlet gating based on a GMM model
@author: ngdavid
"""

__author__ = "David Ng, MD"
__copyright__ = "Copyright 2014, David Ng"
__license__ = "GPL v3"
__version__ = "0.2"
__maintainer__ = "David Ng"
__email__ = "ngdavid@uw.edu"
__status__ = "Prototype"

from scipy.spatial.distance import cdist
from brewer2mpl import qualitative
from sklearn import mixture
import numpy as np
import matplotlib.pyplot as plt


class GMM_doublet_detection(object):
    def __init__(self,data,classes=4):
        self.FSC = data[['FSC-A','FSC-H']]
        #fit and apply GMM to data to make annotations
        self.class_anno, self.gmm_filter, self.centroids = self.__apply_GMM_filtering(n=classes,filter_prob=0.1,subsize=50000)
        self.__display_gating("/home/ngdavid/Desktop/singlet_gating.png")
        
    def __apply_GMM_filtering(self,n=4,filter_prob=0.1,subsize=50000):
        """
        """
        #make a gaussian mixture model 
        g = mixture.GMM(n_components=n,covariance_type='full')

        #make subgroup size the lesser of subsize or len of array
        input_length = len(self.FSC)
        if input_length > subsize:
            subgroup = subsize
        if input_length < 1000:
            raise(ValueError,"Number of events is too small to use this method")
        else:
            subgroup = input_length
        
        # fit on subgroup and predict class probabities on full data
        temp = self.FSC[np.all(self.FSC>0,axis=1)]
        g.fit(temp[:subgroup]) 
        centroids = g.means_
        clf_data = g.predict(self.FSC.values)
        
        # classifiction probablities
        clf_prob = g.predict_proba(self.FSC.values)
        gmm_filter = np.any(clf_prob>filter_prob,axis=1)
        return clf_data,gmm_filter,centroids
    
    def __choose_classes(self):
        
        exclude = [[1,0]]
                self.centroids,exclude
           
    def __display_gating(self,filename,display_points=30000):
        """print a plot of clusters to a file"""
        colors = qualitative.Set1[4]
                
        plt.figure()
        #plt.hold(True)
        for i in np.unique(self.class_anno):
            plt_data = self.FSC[np.all([self.gmm_filter,self.class_anno==i],
                                axis=0)][:display_points]
            plt.plot(plt_data['FSC-A'],plt_data['FSC-H'],'.',
                     markersize=1,c=colors.mpl_colors[i])
            plt.plot(self.centroids[i,0],self.centroids[i,1],'x',
                     markersize=10,mew=4,c=[0,0,0])
        plt.xlabel('FSC-A')
        plt.ylabel('FSC-H')
        plt.show()
        plt.savefig(filename, dpi=500, bbox_inches='tight')

        
if __name__ == "__main__":
    pass
    
