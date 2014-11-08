# -*- coding: utf-8 -*-
"""
Created on Sat 8 Nov 2014

This file describes a class that generates columnwise stats and histograms
from FCS data
@author: David Ng, MD
"""
import pandas as pd
import numpy as np

class Extract_HistoStats(object):
    def __init__(self,FCS):

        self.data = FCS.data
        return self._make_stats()

    def _make_histogram(self,bins=100,range=(0,1),density=True):
        """
        Makes histogram
        :param bins:
        :param range:
        :param density:
        :return:
        """
        columns = self.data.columns
        function_hist = lambda x: np.histogram(x,bins=bins,range=range,density=density)[0]
        histo_df = np.apply_along_axis(function_hist, 0, self.data[columns])
        histo_df = pd.DataFrame(histo_df,columns=columns,index=np.linspace(range[0],range[1],num=bins))
        return histo_df
    def _make_stats(self):
        return self.data.describe
