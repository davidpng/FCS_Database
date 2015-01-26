# -*- coding: utf-8 -*-
"""
Created on Sat 24 Jan 2015 05:19:00 AM PST 
Provides Auto Singlet gating based on a GMM model
@author: ngdavid
"""

__author__ = "David Ng, MD"
__copyright__ = "Copyright 2014, David Ng"
__license__ = "GPL v3"
__version__ = "0.1"
__maintainer__ = "David Ng"
__email__ = "ngdavid@uw.edu"
__status__ = "Prototype"


from sklearn import mixture
import numpy as np
import matplotlib.pyplot as plt
#from brewer2mpl import qualitative

class GMM_double_detection(object):
    def __init__(self,data,classes=4):
        self.FSC = data[['FSC-A','FSC-H']]
       
        #fit and apply GMM to data to make annotations
        self.class_anno, self.gmm_filter = self.__apply_GMM_filtering(n=classes,filter_prob=0.1,subsize=50000)
        
    def __apply_GMM_filtering(self,n=4,filter_prob,subsize):
        """
        """
        #make a gaussian mixture model 
        g = mixture.GMM(n_components=n,covariance_type='full')

        #make subgroup size the lesser of subsize or len of array
        if len(self.FCS) > subsize:
            subgroup = subsize
        if len(self.FCS) < 1000:
            raise(ValueError,"Number of events is too small to use this method")
        else:
            subgroup = len(self.FCS)
            
        # fit on subgroup and predict class probabities on full data
        temp = self.FSC[np.all(FSC>0,axis=1)].values
        g.fit(temp[:subgroup]) 

        clf_data = g.predict(self.FSC.values)
        # classifiction probablities
        clf_prob = g.predict_proba(self.FSC.values)
        gmm_filter = np.any(clf_prob>fliter_prob,axis=1)
        return clf_data,gmm_filter
    
    def __choose_classes(self):
        pass
           
    def __display_gating(self,filename):
        pass
        """
        plt.figure()
        for i in np.unique(clf_data):
            plt_data = self.FCS[np.all([gmm_filter,clf_data==i],axis=0)]
            plt.plot(plt_data[:20000,0],plt_data[:20000,1],',',c=colors.mpl_colors[i])
        plt.savefig(filename, dpi=500, bbox_inches='tight')
        """
if __name__ == "__main__":
    
