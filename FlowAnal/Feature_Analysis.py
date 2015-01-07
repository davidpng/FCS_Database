#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" 
Created on Tue 06 Jan 2015 03:43:24 PM PST 
This file describes a machine learning and feature analysis tools
for analyzing annotated case/feature dataframes

@author: David Ng, MD
"""

import numpy as np
import scipy as sp
import pandas as pd
import os
import logging

from sklearn.svm import SVC
from sklearn.ensemble import  RandomForestClassifier
from sklearn.cross_validation import cross_val_score


log = logging.getLogger(__name__)



class Feature_Analysis(object):
    def __init__(self,features_DF,annotation_DF,threads=4,**kwargs):
        self.features=features_DF
        self.annotations=annotation_DF


        #take or make a report directory        
        if "report_dir" in kwargs:
            self.report_dir = kwargs["report_dir"]
        else:
            self.report_dir = "data_report"
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
        
    def classifer_setup(self,Type='SVM',**kwargs):
        if Type.lower() == 'svm':
            self.classifer = svm.SVC(kernal='RBF')
        elif Type.lower() == 'rfc':
            self.classifer = ens.RandomForestClassifier(**kwargs)
        else:
            raise TypeError('Classifier Type undefined')
    
    def prototype_analysis(self,**kwargs):
        clf = RandomForestClassifier(n_estimators=200, n_jobs=4, **kwargs)
        
        scores = cross_val_score(estimator = clf,
                                 X=self.features.value,
                                 y=self.annotations.value,
                                 cv=8, n_jobs=6, pre_dispatch=20)
        
        filename = "Prototype_Analysis_Report.txt"
        out_string = "mean score is: {:.03f} +/- {:.03f}".format(scores.mean(),scores.std())
        
        fh = open(os.path.join(self.report_dir,filename),'w')
        fh.write(out_string)
        fh.close()
        
