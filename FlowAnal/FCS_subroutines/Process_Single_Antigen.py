# -*- coding: utf-8 -*-
"""
Created on Fri Oct 24 15:03:23 2014
Provides Compensation and scaling functionality
@author: ngdavid
"""

__author__ = "Dan Herman"
__copyright__ = "Copyright 2015, Daniel Herman"
__license__ = "GPL v3"
__version__ = "1.0"

# import scipy as sp
import sklearn as sk
import numpy as np
import pandas as pd
from math import floor
from os.path import relpath, dirname
import logging
log = logging.getLogger(__name__)

from FlowAnal.FCS_subroutines.Process_FCS_Data import Gate_2D


def UL_gate(bottom=1e3, top=(2**18)*0.95):
    """ Return uppper left corner gate """
    return ((0, bottom), (0.9*bottom, bottom), (top * 0.95, top),
            (0, top), (0, bottom))


def check_signal(vals, min_pos=50, pos_threshold=2e3, range_threshold=10):
    """ Return whether vals meets criteria """

    val_range = np.percentile(vals, [1, 99])
    return (len(np.where(vals > pos_threshold)[0]) >= min_pos) and \
        ((val_range[1]/val_range[0]) > range_threshold)


class Process_Single_Antigen(object):
    """
    Process single antigen flow data to estimate channel cross-talk
    """

    def __init__(self, FCS, dir):

        self.FCS = FCS
        self.filepath = self.FCS.filepath
        self.empty = self.FCS.empty
        self.fits = []
        self.gate = {}
        if self.empty is False:
            log.debug('Processing "{}" OLD: {}'.format(self.FCS.filename, self.FCS.old))
            self.added_col = self.FCS.single_antigen['Column Name']
            self.cols_i, self.cols = self.FCS.get_fluorophore_channels()
            self.make_meta(dir)
            self.check_signal()  # toggle self.empty

    def check_signal(self, min_pos=50, pos_threshold=2e3,
                     range_threshold=10):
        """ Convert to empty if no positive data """
        vals = self.FCS.data[self.added_col].values
        if not check_signal(vals, min_pos, pos_threshold, range_threshold):
            self.empty = True
            self.flag = 'Not enough signal to process'
            self.error_message = 'No signal'
            log.info('Skipping {} because not enough signal'.format(self.filepath))

    def fit_Comp(self, model='RANSAC', fit_w_FSC=True, best_cluster=False,
                 **kwargs):

        if hasattr(self.FCS, 'cluster'):
            self.Calculate_Comp_clustered(add_gate=False, model=model,
                                          downsample_on_y=False, fit_w_FSC=fit_w_FSC,
                                          best_cluster=best_cluster)
        else:
            self.fits.append(self.Calculate_Comp(add_gate=False, model=model,
                                                 fit_w_FSC=fit_w_FSC,
                                                 downsample_on_y=False))
            self.fits.append(self.Calculate_Comp(add_gate=False, model=model,
                                                 fit_w_FSC=fit_w_FSC,
                                                 downsample_on_y=True))
        if best_cluster and len(self.fits) > 0:
            self.pick_comp()

    def Calculate_Comp_clustered(self, add_gate, model, downsample_on_y, fit_w_FSC,
                                 min_pos=30, pos_threshold=2e3,
                                 range_threshold=10, best_cluster=False):
        """ Cycle through all clusters in self.FCS.cluster and
        for all meeting criteria, fit line
        """

        def group_pick_row(x):
            """ Pick row that has the lowest slope within the decile of score """
            max_score = max(x.score.values)
            if max_score > 0:
                which_max = np.where(x.score.values >= max_score * 0.9)[0]
            else:
                which_max = np.where(x.score.values >= max_score * 1.1)[0]
            # counts = np.digitize(x.score.values, bins=np.linspace(-0.5, 1, num=15))
            # max_count = max(counts)
            # which_max = np.where(counts == max_count)[0]
            if len(which_max) == 1:
                row_mask = x.index[which_max[0]]
            else:
                min_slope = min(x.m.values[which_max])
                which_min = np.intersect1d(np.where(x.m.values == min_slope)[0], which_max,
                                           assume_unique=True)
                row_mask = x.index[which_min[0]]
            return x.loc[row_mask, :]

        for c in np.unique(self.FCS.cluster[self.FCS.cluster >= 0]):
            vals = self.FCS.data[self.added_col].values[self.FCS.cluster == c]

            if check_signal(vals, min_pos, pos_threshold, range_threshold):
                a = self.Calculate_Comp(add_gate=add_gate, model=model, fit_w_FSC=fit_w_FSC,
                                        downsample_on_y=False, cluster=c)
                b = self.Calculate_Comp(add_gate=add_gate, model=model, fit_w_FSC=fit_w_FSC,
                                        downsample_on_y=True, cluster=c)
                res = pd.concat([a, b])
                res.reset_index(inplace=True, drop=True)

                if best_cluster:
                    resg = res.groupby(['xt_Channel_Number'])
                    res2 = resg.apply(group_pick_row)
                    res2.reset_index(inplace=True, drop=True)
                    self.fits.append(res2)
                else:
                    self.fits.append(res)

    def pick_comp(self):

        res = pd.concat(self.fits)
        res.reset_index(inplace=True, drop=True)

        # Pick the cell population to use for everything, then go with that one!
        # Perhaps rank order each one and pick the cluster with the lowest cumulative rank

        def group_pick_row(x):
            n_scores_pos = x.score.values > -0.01
            if np.sum(n_scores_pos) == 1:
                row_mask = n_scores_pos
            elif np.sum(n_scores_pos) == 0:
                row_mask = x.index == x.m.argmin()
            else:
                n_min_pos = x.m.values == x.m.loc[n_scores_pos].min()
                if np.sum(n_min_pos) > 1:
                    n_min_pos = x.index == np.where(n_min_pos)[0][0]
                row_mask = n_min_pos

            return x.loc[row_mask, :]

        resg = res.groupby(['xt_Channel_Number'])
        res2 = resg.apply(group_pick_row)
        res2.reset_index(inplace=True, drop=True)

        self.final_fit = res2

    def Calculate_Comp(self, max_cells=int(1e5), add_gate=False,
                       UL_gate_bottom=1e3,
                       downsample_on_y=False,
                       cluster=None,
                       model='RANSAC',
                       nbins=40,
                       fit_w_FSC=True):
        """ Calculate the cross-talk array """

        added_col = self.added_col
        self.gate = {}

        # Pick cells to use
        res = []
        for c in self.cols:

            # Gate_2D
            if c != added_col and add_gate is True:
                UL_gate_coords = UL_gate(bottom=UL_gate_bottom)
                cells = Gate_2D(self.FCS.data, c, added_col,
                                UL_gate_coords)
                self.gate[c] = UL_gate_coords
                cells_i = np.where(cells)[0]
            else:
                cells_i = np.arange(self.FCS.data.shape[0])
            log.debug("Columns: {}, {} => Cells: {}".format(added_col, c, len(cells_i)))

            if cluster is not None:
                cells_i = np.intersect1d(cells_i,
                                         np.where(self.FCS.cluster == cluster)[0],
                                         assume_unique=True)

            # Downsample in dense areas based on added_col
            if downsample_on_y is True:
                bins = np.logspace(0, 18, base=2, num=nbins)
                bin_membership = np.digitize(self.FCS.data[added_col].values[cells_i], bins)
                bin_counts = np.bincount(bin_membership, minlength=nbins)
                mean_count = float(np.mean(bin_counts[np.where(bin_counts >= 5)[0]]))
                tmp_i = []
                for i in range(nbins):
                    if bin_counts[i] > mean_count:
                        count = bin_counts[i]
                        n_to_include = floor(mean_count * (1 + np.log10(count / mean_count)))
                        tmp = np.random.choice(np.where(bin_membership == i)[0],
                                               size=n_to_include, replace=False)
                        tmp_i.extend(cells_i[tmp])
                    else:
                        tmp = np.where(bin_membership == i)[0]
                        tmp_i.extend(cells_i[tmp])
                cells_i = np.asarray(tmp_i)
                log.debug("Downsampled to {}".format(len(cells_i)))

            # Downsample randomly
            if len(cells_i) > max_cells:
                cells_i = np.random.choice(cells_i, size=max_cells, replace=False)

            # Solve for cross-talk
            x = self.solve_crosstalk(cells_i, added_col, c, model, fit_w_FSC)
            res.append(x)

        meta = self.meta
        meta.set_index(['xt_Channel_Number'], drop=False, inplace=True)
        res = pd.DataFrame(np.vstack(res), index=self.cols_i, columns=['m', 'm2', 'b', 'N', 'score'])
        self.res = pd.concat((self.meta, res), axis=1)
        self.res.reset_index(inplace=True, drop=True)

        self.res['model'] = model
        self.res['downsample_on_y'] = downsample_on_y
        if add_gate is True:
            self.res['gate'] = downsample_on_y
        else:
            self.res['gate'] = None
        self.res['cluster'] = cluster
        return self.res

    def solve_crosstalk(self, i, in_col, out_col, model='RANSAC', fit_w_FSC=True,
                        pos_threshold=2e3):
        """ Estimate the linear cross-talk from in_col to out_col """

        # a = np.ones((len(i), 2))
        # a[:, 0] = self.FCS.data[in_col].values[i]
        if fit_w_FSC is True:
            a = self.FCS.data[[in_col, 'FSC-H']].values[i]
            a.shape = (len(i), 2)
        else:
            a = self.FCS.data[in_col].values[i]
            a.shape = (len(i), 1)

        y = self.FCS.data[out_col].values[i]
        # y.shape = (len(i), 1)

        # TODO: add non-negative back as an option
        # x, res = sp.optimize.nnls(a, y)
        # model = sk.linear_model.LinearRegression()
        # Try adding FSC-A as a parameter
        if model == 'RANSAC':
            model = sk.linear_model.RANSACRegressor(sk.linear_model.LinearRegression())
            model.fit(a, y)
            x = model.estimator_
            coef = x.coef_[0, 0]
            score = model.score(a, y)
            intercept = x.intercept_[0]
            if len(x.coef_[0, :]) > 1:
                coef2 = x.coef_[0, 1]
            else:
                coef2 = None
        elif model == 'LINEAR':
            model = sk.linear_model.LinearRegression()
            model.fit(a, y)
            coef = model.coef_[0]
            score = model.score(a, y)
            intercept = model.intercept_
            if len(model.coef_) > 1:
                coef2 = model.coef_[1]
            else:
                coef2 = None
        return (coef, coef2, intercept, len(i), score)

    def make_meta(self, dir):
        """ Push crosstalk info to db """

        self.meta = pd.DataFrame({'comp_tube_idx': self.FCS.comp_tube_idx,
                                  'filename': self.FCS.filename,
                                  'xt_Channel_Number': self.cols_i,
                                  'date': str(self.FCS.date),
                                  'cytnum': self.FCS.cytnum,
                                  'Antigen': self.FCS.single_antigen['Antigen'],
                                  'Fluorophore': self.FCS.single_antigen['Fluorophore'],
                                  'Channel_Name': self.FCS.single_antigen['Column Name'],
                                  'Channel_Number': self.FCS.single_antigen['Channel_Number'],
                                  'old': str(self.FCS.old)})

        if self.FCS.filepath != 'Does not exist' and dir is not None:
            self.meta['dirname'] = relpath(dirname(self.FCS.filepath), start=dir)
        else:
            self.meta['dirname'] = 'Does not exist'

    def push_db(self, db):

        if hasattr(self, 'res'):
            db.add_df(df=self.res, table='SingleComp')
        else:
            db.add_df(df=self.meta, table='SingleComp')

    def plot(self, name='test'):
        """ Plot out results """
        col_i = np.where(self.FCS.parameters.columns.values == \
                         self.FCS.single_antigen['Column Name'])[0][0]
        outfile = 'output/' + '_'.join([name,
                                        self.FCS.single_antigen['Column Name'].replace(' ', '_'),
                                        str(self.FCS.comp_tube_idx),
                                        'SingleAntigen',
                                        self.FCS.date.strftime("%Y%m%d"),
                                        self.FCS.cytnum,
                                        'comp_fit'])
        self.FCS.visualize_2D(outfile=outfile, vizmode='SingleAntigen',
                              comp_lines=self.fits, gate=self.gate,
                              logit=True,
                              col_i=col_i)
