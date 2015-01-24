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
import scipy.signal as signal
import numpy as np
import matplotlib.pyplot as plt
import logging
log = logging.getLogger(__name__)

class GMM_doublet_detection(object):
    def __init__(self,data,classes=4,singlet_verbose=False,**kwargs):
        self.num_classes = classes
        self.FSC = data[['FSC-A','FSC-H']]
        #fit and apply GMM to data to make annotations
        self.class_anno, self.gmm_filter, self.centroids = self.__apply_GMM_filtering(n=classes,filter_prob=0.15,**kwargs)
        self.singlet_mask = self.__choose_classes_radial()
        
        if singlet_verbose==True:
            self.__display_gating("/home/ngdavid/Desktop/singlet_gating.png") #find a place to put theses?
            self.__display_mask("/home/ngdavid/Desktop/singlet_mask.png")
                    
    def calculate_stats(self):
        """
        This function generates statistics about the loss fraction of the filter
        """
        number_lost = np.sum(self.singlet_mask)
        percentage_lost = float(number_lost)/len(self.FSC)
        return number_lost, percentage_lost
        
    def __apply_GMM_filtering(self,n=4,filter_prob=0.1,subsize=50000,**kwargs):
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
        """Chooses class to use 
        Returns an output mask
        """
        exclude = [[1,0]]
        class_distances = cdist(self.centroids,exclude,"euclidean")
        class_to_dismiss = np.argmin(class_distances)
        
        log.info("number {} class was dismissed as a double region".format(class_to_dismiss))
        output = self.class_anno!=class_to_dismiss
        output = output * self.gmm_filter
        return output
        
    def __choose_classes_radial():
        """Chooses class to use using a filter rebasis of the point locations
        Returns an output mask
        """
        origin = [[0,0]]
        xy = self.centroids - np.array(origin)
        theta = np.atan(xy[:,1]/xy[:,0])
        print theta
        
        basis, basis_space = np.histogram(theta,bins=60,range=(0,1.2))
        filtered_basis = signal.weiner(basis)
        print filtered_basis
        return None
        
    def __display_gating(self,filename,display_points=30000):
        """print a plot of clusters to a file"""
        colors = qualitative.Set1[self.num_classes]
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
        plt.xlim(0,1)
        plt.ylim(0,1)
        plt.title("Number of classes: {}\nNumber of events: {}".format(self.num_classes,len(self.FSC)))
        plt.show()
        plt.savefig(filename, dpi=500, bbox_inches='tight')
       
    def __display_mask(self,filename,display_points=30000):
        """print a plot of clusters to a file"""
        
        plt.figure()
        plt.plot(self.FSC[self.singlet_mask]['FSC-A'],
                 self.FSC[self.singlet_mask]['FSC-H'],
                 'b.',markersize=1)
        plt.xlabel('FSC-A')
        plt.ylabel('FSC-H')
        plt.xlim(0,1)
        plt.ylim(0,1)
        plt.title("Number of classes: {}\nNumber of events: {}".format(self.num_classes,len(self.FSC)))
        plt.show()
        plt.savefig(filename, dpi=500, bbox_inches='tight')

        
if __name__ == "__main__":
    pass
    
