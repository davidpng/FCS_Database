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
from math import ceil
from os.path import relpath, dirname
import logging
log = logging.getLogger(__name__)

from FlowAnal.FCS_subroutines.Process_FCS_Data import Gate_2D


def UL_gate(bottom=1e3, top=(2**18)*0.95):
    """ Return uppper left corner gate """
    return ((0, bottom), (0.9*bottom, bottom), (top * 0.95, top),
            (0, top), (0, bottom))


class Process_Single_Antigen(object):
    """
    Process single antigen flow data to estimate channel cross-talk
    """

    def __init__(self, FCS, dir):

        self.FCS = FCS
        self.filepath = self.FCS.filepath
        self.empty = self.FCS.empty
        self.fits = []
        if self.empty is False:
            log.debug('Processing "{}" OLD: {}'.format(self.FCS.filename, self.FCS.old))
            self.added_col = self.FCS.single_antigen['Column Name']
            self.cols_i, self.cols = self.FCS.get_fluorophore_channels()
            self.make_meta(dir)

    def fit_Comp(self):
        added_col = self.FCS.single_antigen['Column Name']

        if 'CD45' in added_col:
            self.Calculate_Comp(add_gate=False, model='RANSAC', downsample_on_y=False)
            self.Calculate_Comp(add_gate=False, model='RANSAC', downsample_on_y=True)
            self.pick_comp()
        else:
            self.Calculate_Comp(add_gate=False, model='RANSAC', downsample_on_y=False)
            self.Calculate_Comp(add_gate=False, model='RANSAC', downsample_on_y=True)
            self.pick_comp()

    def pick_comp(self):

        res = pd.concat(self.fits)
        res.reset_index(inplace=True, drop=True)

        def group_pick_row(x):
            n_scores_pos = x.score.values > 0.1
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
                       model='RANSAC'):
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

            # Downsample in dense areas based on added_col
            if downsample_on_y is True:
                bins = np.logspace(0, 18, base=2, num=40)
                bin_membership = np.digitize(self.FCS.data[added_col], bins)
                bin_counts = np.bincount(bin_membership, minlength=100)
                mean_count = float(np.mean(bin_counts[np.where(bin_counts >= 5)[0]]))
                tmp_i = []
                for i in range(len(bins)):
                    if bin_counts[i] > mean_count:
                        count = bin_counts[i]
                        n_to_include = ceil(mean_count * (1 + np.log10(count / mean_count)))
                        tmp = np.random.choice(np.where(bin_membership == i)[0],
                                               size=n_to_include, replace=False)
                        tmp_i.extend(tmp)
                    else:
                        tmp_i.extend(np.where(bin_membership == i)[0])
                cells_i = np.asarray(tmp_i)
                log.debug("Downsampled to {}".format(len(cells_i)))

            # Downsample randomly
            if len(cells_i) > max_cells:
                cells_i = np.random.choice(cells_i, size=max_cells, replace=False)

            # Solve for cross-talk
            x = self.solve_crosstalk(cells_i, added_col, c, model)
            res.append(x)

        meta = self.meta
        meta.set_index(['xt_Channel_Number'], drop=False, inplace=True)
        res = pd.DataFrame(np.vstack(res), index=self.cols_i, columns=['m', 'b', 'N', 'score'])
        self.res = pd.concat((self.meta, res), axis=1)
        self.res.reset_index(inplace=True, drop=True)

        self.res['model'] = model
        self.res['downsample_on_y'] = downsample_on_y
        if add_gate is True:
            self.res['gate'] = downsample_on_y
        else:
            self.res['gate'] = None
        self.fits.append(self.res)

    def solve_crosstalk(self, i, in_col, out_col, model='RANSAC'):
        """ Estimate the linear cross-talk from in_col to out_col """

        # a = np.ones((len(i), 2))
        # a[:, 0] = self.FCS.data[in_col].values[i]
        a = self.FCS.data[in_col].values[i]
        a.shape = (len(i), 1)

        y = self.FCS.data[out_col].values[i]
        # y.shape = (len(i), 1)

        # TODO: add non-negative back as an option
        # x, res = sp.optimize.nnls(a, y)
        # model = sk.linear_model.LinearRegression()
        if model == 'RANSAC':
            model = sk.linear_model.RANSACRegressor(sk.linear_model.LinearRegression())
            model.fit(a, y)
            x = model.estimator_
            score = model.score(a, y)
            log.debug("Channel: {}, Trials: {}".format(out_col, model.n_trials_))
            return (x.coef_[0, 0], x.intercept_[0], len(i), score)
        elif model == 'LINEAR':
            model = sk.linear_model.LinearRegression()
            model.fit(a, y)
            score = model.score(a, y)
            return (model.coef_[0], model.intercept_, len(i), score)

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

    def plot(self):
        """ Plot out results """
        col_i = np.where(self.FCS.parameters.columns.values == \
                         self.FCS.single_antigen['Column Name'])[0][0]
        outfile = 'output/' + '_'.join([str(self.FCS.comp_tube_idx),
                                        'SingleAntigen',
                                        self.FCS.date.strftime("%Y%m%d"),
                                        self.FCS.single_antigen['Column Name'].replace(' ', '_'),
                                        'comp_fit'])
        self.FCS.visualize_2D(outfile=outfile, vizmode='SingleAntigen',
                              comp_lines=self.fits, gate=self.gate,
                              logit=True,
                              col_i=col_i)
