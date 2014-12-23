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

    def __init__(self, FCS):
        """
        Returns 2 dataframes, stats and histogram indexed on parameters in
        FCS.data
        TODO: Other statistical Measures to be added?
        :param FCS:
        :return:
        """
        if hasattr(FCS, 'data'):
            self.FCS = FCS
            FCS.PmtStats = self.__make_PmtStats()
            FCS.TubeStats = self.__make_TubeStats()
            FCS.histos = self.__make_histogram()
            log.debug(FCS.PmtStats)
            log.debug(FCS.TubeStats)
            log.debug(FCS.histos)
        else:
            log.debug('Nothing todo because stats and histogram are missing')

    def __make_histogram(self, bins=100, range=(0, 1), density=True):
        """
        Makes histogram with bins defined by bins over a normalized range of [0,1)
        Columns are indexed on parameters (scatter, antigens, & time)
        Rows are indexed on bin location
        :param bins:
        :param range:
        :param density:
        :return pandas dataframe:
        """
        columns = self.FCS.data.columns
        function_hist = lambda x: np.histogram(x, bins=bins, range=range, density=density)[0]
        histo_df = np.apply_along_axis(function_hist, 0, self.FCS.data[columns])
        histo_df = pd.DataFrame(histo_df, columns=columns,
                                index=np.linspace(range[0], range[1], num=bins))
        return histo_df

    def __make_PmtStats(self):
        """
        Returns a dataframe with columns indexed on parameters
        Rows of [count,mena,std,min,25%,50%,75%,max]
        :return:
        """
        stats = self.FCS.data.describe().T

        # Add transformation filtering information
        stats = pd.concat([stats, self.FCS.n_transform_keep_by_channel], axis=1, join='outer',
                          ignore_index=False)
        stats = pd.concat([stats, self.FCS.n_transform_not_nan_by_channel], axis=1, join='outer',
                          ignore_index=False)

        return stats

    def __make_TubeStats(self):
        """
        Returns a dataframe with columns indexed on Case_tube
        Rows of [...]
        :return:
        """
        stats = {}

        # Add filtering information
        stats['total_events'] = self.FCS.total_events
        stats['transform_in_limits'] = self.FCS.n_transform_keep_all
        stats['transform_not_nan'] = self.FCS.n_transform_not_nan_all
        if hasattr(self.FCS, 'viable_remain'):
            stats['viable_remain'] = self.FCS.viable_remain
        if hasattr(self.FCS, 'singlet_remain'):
            stats['singlet_remain'] = self.FCS.singlet_remain

        return stats
