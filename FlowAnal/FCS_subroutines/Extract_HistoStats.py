# -*- coding: utf-8 -*-
"""
Created on Sat 8 Nov 2014

This file describes a class that generates column-wise stats and histograms
from FCS data
@author: David Ng, MD
"""
import pandas as pd
import numpy as np
import logging

log = logging.getLogger(__name__)


class Extract_HistoStats(object):

    def __init__(self, FCS, verbose=False):
        """
        Returns 2 dataframes, stats and histogram indexed on parameters in
        FCS.data
        TODO: Other statistical Measures to be added?
        :param FCS:
        :param verbose:
        :return:
        """
        if hasattr(FCS, 'data'):
            self.data = FCS.data
            FCS.stats = self._make_stats()
            FCS.histos = self._make_histogram()
            if verbose:
                print "Parameters Statistics:\n"
                print FCS.stats
                print "Parameter Histograms:\n"
                print FCS.histos
        else:
            log.debug('Nothing todo because stats and histogram are missing')

    def _make_histogram(self, bins=100, range=(0, 1), density=True):
        """
        Makes histogram with bins defined by bins over a normalized range of [0,1)
        Columns are indexed on parameters (scatter, antigens, & time)
        Rows are indexed on bin location
        :param bins:
        :param range:
        :param density:
        :return pandas dataframe:
        """
        columns = self.data.columns
        function_hist = lambda x: np.histogram(x, bins=bins, range=range, density=density)[0]
        histo_df = np.apply_along_axis(function_hist, 0, self.data[columns])
        histo_df = pd.DataFrame(histo_df, columns=columns,
                                index=np.linspace(range[0], range[1], num=bins))
        return histo_df

    def _make_stats(self):
        """
        Returns a dataframe with columns indexed on parameters
        Rows of [count,mena,std,min,25%,50%,75%,max]
        :return:
        """
        return self.data.describe()
