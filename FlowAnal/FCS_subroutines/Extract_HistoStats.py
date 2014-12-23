# -*- coding: utf-8 -*-
"""
Created on Sat 8 Nov 2014

This file describes a class that generates column-wise stats and histograms
from FCS data
@author: David Ng, MD
"""
from scipy.stats import pearsonr
from matplotlib.path import Path

import pandas as pd
import numpy as np

import logging
import itertools

log = logging.getLogger(__name__)

class Extract_HistoStats(object):

    def __init__(self, FCS,range=(0,1),comp_corr_cutoff=10):
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
            FCS.histos = self.__make_histogram(range=range)
            FCS.comp_correlation, FCS.comp_p_value = self.__generate_comp_corr_mtx(cutoff=comp_corr_cutoff)
            """ Moved to test_FCS.py
            log.debug(FCS.PmtStats)
            log.debug(FCS.TubeStats)
            log.debug(FCS.histos)
            log.debug(FCS.comp_correlation)
            """
        else:
            log.debug('Nothing todo because stats and histogram are missing')

    def __make_histogram(self, range, bins=100, density=True):
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

    def __generate_comp_corr_mtx(self, cutoff=50):
        """
	    This function generates a square matrix as a pandas dataframe listing the 
	    Pearson's correlation coefficient for each channel/reagent combination
		
	    Takes arguments:
	    cutoff - required number of events in the gated 'high comp' area (default 50)
	    Returns:
	    correlation_mtx - a correlation matrix with rows and columns as reagents \
	                      describing the dispersion correlation between pairs 
					      (rows,columns)
					      The diagonal of this should be all ones
	    p_value_mtx - a dataframe describing the p_value (measure of significace \
	                  given the size and correlation)
        N.B. - This is a subfunction of the FCS object
	    """
        # set up the reagent list 
        exclude = ['FSC-A','FSC-H','SSC-A','SSC-H','Time']
        reagents = [i for i in self.FCS.data.columns if i not in exclude] 

        # make an empty dataframe to take information
        sq_ones = np.ones((len(reagents),len(reagents)))
        sq_ones[:] = np.nan
        correlation_mtx = pd.DataFrame(sq_ones, index=reagents, columns=reagents)
        p_value_mtx =  pd.DataFrame(sq_ones, index=reagents, columns=reagents)

        for (x,y) in itertools.permutations(reagents,2):
	        # this will walk through all pairwise permutations of the reagent
            correlation = self.__comp_correlation(x,y,cutoff=cutoff)
            correlation_mtx[x][y] = correlation[0]
            p_value_mtx[x][y] = correlation[1]

        return correlation_mtx,p_value_mtx

    def __comp_correlation(self,x_ax,y_ax,cutoff):
        gated_pop = self.FCS.data[[x_ax,y_ax]][self.__UL_gating(x_ax,y_ax)]
        
        if len(gated_pop) > cutoff:
	        output = pearsonr(gated_pop.iloc[:,0],gated_pop.iloc[:,1])

        else: 
	          #if not enough events exist in the gate; there is no point in taking
	          #a correlation and we should append NaN to the matrix
	        output = (np.nan,np.nan)
        return output
        
    def __UL_gating(self,x_ax,y_ax):
        #describes an upper left corner gate
        coords = [(0.0,0.7),(0.6,0.7),(0.9,1.0),(0.0,1.0),(0.0,0.7)]
        gate = Path(coords, closed=True)
        projection = np.array(self.FCS.data[[x_ax, y_ax]])
        index = gate.contains_points(projection)
        return index

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
