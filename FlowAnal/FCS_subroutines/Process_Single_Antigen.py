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
from FlowAnal.Analysis_Variables import gate_coords
from FlowAnal.FCS_subroutines.Process_FCS_Data import Gate_2D

import logging
log = logging.getLogger(__name__)


class Process_Single_Antigen(object):
    """
    Process single antigen flow data to estimate channel cross-talk
    """

    def __init__(self, FCS):

        self.FCS = FCS
        self.filepath = self.FCS.filepath
        self.empty = self.FCS.empty
        if self.empty is False:
            log.debug('Processing "{}" OLD: {}'.format(self.FCS.filename, self.FCS.old))

    def Calculate_Comp(self, max_cells=int(1e5), add_gate=False,
                       gate=gate_coords['UL_linear']['coords'],
                       model='RANSAC'):
        """ Calculate the cross-talk array """

        added_col = self.FCS.single_antigen['Column Name']
        cols_i, cols = self.FCS.get_fluorophore_channels()
        self.gate = {}

        # Pick cells to use
        res = []
        for c in cols:
            if c != added_col and add_gate is True:
                cells = Gate_2D(self.FCS.data, c, added_col,
                                gate)
                self.gate[c] = gate
                cells_i = np.where(cells)[0]
            else:
                cells_i = np.arange(self.FCS.data.shape[0])
            log.debug("Columns: {}, {} => Cells: {}".format(added_col, c, len(cells_i)))

            if len(cells_i) > max_cells:
                cells_i = np.random.choice(cells_i, size=max_cells, replace=False)

            # Solve for cross-talk
            x = self.solve_crosstalk(cells_i, added_col, c, model)
            res.append(x)
        res = np.vstack(res)
        self.res = pd.DataFrame(res, index=cols_i, columns=['m', 'b', 'N', 'score'])
        self.make_results()

    def solve_crosstalk(self, i, in_col, out_col, model='RANSAC', downsample_on_y=True):
        """ Estimate the linear cross-talk from in_col to out_col """

        # a = np.ones((len(i), 2))
        # a[:, 0] = self.FCS.data[in_col].values[i]
        a = self.FCS.data[in_col].values[i]
        a.shape = (len(i), 1)

        y = self.FCS.data[out_col].values[i]
        # y.shape = (len(i), 1)

        if downsample_on_y is True:
            bins = np.logspace(0, 18, base=2, num=20)
            bin_membership = np.digitize(y, bins)
            bin_counts = np.bincount(bin_membership)
            bins_to_use = np.where(bin_counts >= 50)[0]
            mean_count = np.mean(bin_counts[bins_to_use])

            s = []
            for x in bins_to_use:
                count = bin_counts[x]
                if bin_counts[x] < mean_count:
                    tmp = np.random.choice(np.where(bin_membership == x)[0],
                                           size=count * 3, replace=True)
                else:
                    tmp = np.random.choice(np.where(bin_membership == x)[0],
                                           size=count / 3, replace=True)
                s.extend(tmp)
            s = np.asarray(s)
            s = np.ravel(s)
            a = a[s]
            y = y[s]

        # TODO: add non-negative back as an option
        # x, res = sp.optimize.nnls(a, y)
        # model = sk.linear_model.LinearRegression()
        if model == 'RANSAC':
            model = sk.linear_model.RANSACRegressor(sk.linear_model.LinearRegression())
            model.fit(a, y)
            x = model.estimator_
            score = model.score(a, y)
            print "Channel: {}, Trials: {}".format(out_col, model.n_trials_)
            return (x.coef_[0, 0], x.intercept_[0], len(i), score)
        elif model == 'LINEAR':
            model = sk.linear_model.LinearRegression()
            model.fit(a, y)
            score = model.score(a, y)
            return (model.coef_[0], model.intercept_, len(i), score)

        # If I downsample, how do i distinguish between real and crap?
        # errors in y versus x axis

        # Downsample, don't upsample
        # Plot multiple lines, think about best-in-breed approach -- full plot, Upper Left, +/- downsample (pick in order and accounting for score and slope)

    def make_results(self):
        """ Push crosstalk info to db """

        self.res['comp_tube_idx'] = self.FCS.comp_tube_idx
        self.res['date'] = str(self.FCS.date)
        self.res['cytnum'] = self.FCS.cytnum
        self.res['Antigen'] = self.FCS.single_antigen['Antigen']
        self.res['Fluorophore'] = self.FCS.single_antigen['Fluorophore']
        self.res['Channel_Name'] = self.FCS.single_antigen['Column Name']
        self.res['old'] = str(self.FCS.old)
        self.res.reset_index(drop=False, inplace=True)
        self.res.columns.values[0] = 'xt_Channel_Number'
        self.res['filename'] = self.FCS.filename

    def push_db(self, db):

        db.add_df(df=self.res, table='SingleComp')

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
                              comp_lines=self.res, gate=self.gate,
                              logit=True,
                              col_i=col_i)
