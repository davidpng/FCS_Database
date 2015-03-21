# -*- coding: utf-8 -*-
"""
Created on Tue 30 Dec 2014 10:29:41 AM PST
This file describes a feature extraction class for N dimensions

@author: David Ng, MD
"""
import pandas as pd
import numpy as np
import scipy as sp

import logging
import itertools
log = logging.getLogger(__name__)


class p2D_Feature_Extraction(object):
    def __init__(self, FCS, bins, exclude_params=['Time'], label_with='Antigen', **kwargs):
        """
        bins = number of bins per axis
        Accessiable Parameters
        type
        bin_description
        histogram
        """

        FCS_data = FCS.data.copy()

        # Switch labels
        new_labs = []
        if label_with is not None:
            for x in FCS_data.columns.tolist():
                colname = FCS.parameters.columns[FCS.parameters.loc['Channel_Name', :] == x][0]
                xlab = FCS.parameters.loc[label_with, colname]
                if xlab is not None:
                    new_labs.append(xlab)
                else:
                    new_labs.append(x)
        FCS_data.columns = new_labs

        # generate list of columns to be used
        columns = [c for c in FCS_data.columns if c not in exclude_params]

        # generate a dictionary describing the bins to be used
        self.bin_description = self._Generate_Bin_Dict(columns, bins)

        self.histogram, self.feature_descriptions = self._flattened_2d_histograms(FCS_data=FCS_data,
                                                                                  columns=columns,
                                                                                  bin_dict=self.bin_description,
                                                                                  **kwargs)

    def _flattened_2d_histograms(self, FCS_data, columns, bin_dict, ul=1.0, normalize=True,
                                 **kwargs):
        """
        """
        features_list = []
        feature_space = []
        for features in itertools.combinations(columns, 2):
            dim = (bin_dict[features[0]], bin_dict[features[1]])
            log.debug(features)
            histo2d, xbin, ybin = np.histogram2d(FCS_data[features[0]],
                                                 FCS_data[features[1]],
                                                 bins=dim,
                                                 range=[[0, ul], [0, ul]],
                                                 normed=normalize)

            #feature_space.extend(np.ravel(1-1/((histo2d*scaling)**0.75+1)))
            feature_space.extend(np.ravel(histo2d))
            features_list.append(('_'.join(features), dim[0] * dim[1]))

        features_list = pd.Series(zip(*features_list)[1], zip(*features_list)[0], dtype=np.int64)
        return sp.sparse.csr_matrix(feature_space), features_list

    def _coord2sparse_histogram(self, vector_length, coordinates, normalize=True,
                                **kwargs):
        """
        generates a sparse matrix with normalized histogram counts
        each bin describes the fraction of total events within it (i.e. < 1)
        """
        output = sp.sparse.lil_matrix((1, vector_length), dtype=np.float32)
        for i in coordinates:
            output[0, i] += 1
        if normalize:
            return output / len(coordinates)
        else:
            return output

    def _Generate_Bin_Dict(self, columns, bins):
        """
        Performs error checking and type converion for bins
        """
        if isinstance(bins, int):
            bin_dict = pd.Series([bins] * len(columns), index=columns)
        elif isinstance(bins, list):
            if len(bins) != len(columns):
                raise RuntimeWarning("number of bins in the list does not match the number of parameters")
            else:
                bin_dict = pd.Series(bins, columns)
        elif isinstance(bins, dict):
            if bins.keys() not in columns or columns not in bins.keys():
                raise RuntimeWarning("The bin keys do not match the provided columns")
            else:
                raise RuntimeWarning("bin dict not implemented")
        else:
            raise TypeError("provided bins parameter is not supported")
        return bin_dict

    def Return_Coordinates(self,index):
        """
        Returns the bin parameters
        """
        pass

