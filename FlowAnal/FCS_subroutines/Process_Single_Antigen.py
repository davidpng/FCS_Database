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
        log.info('Processing "{}" OLD: {}'.format(self.FCS.filename, self.FCS.old))

    def Calculate_Comp(self, max_cells=int(1e5)):
        """ Calculate the cross-talk array """

        added_col = self.FCS.single_antigen['Column Name']
        cols_i = [i for i, x in enumerate(self.FCS.data.columns)
                  if x.upper()[0:3] not in ['FSC', 'SSC', 'TIM']]
        cols = self.FCS.data.columns.values[cols_i]

        # Pick cells to use
        res = []
        for c in cols:
            if c != added_col:
                cells = Gate_2D(self.FCS.data, c, added_col,
                                gate_coords['UL_linear']['coords'])
                cells_i = np.where(cells)[0]
            else:
                cells_i = np.arange(self.FCS.data.shape[0])
            log.debug("Columns: {}, {} => Cells: {}".format(added_col, c, len(cells_i)))

            if len(cells_i) > max_cells:
                cells_i = np.random.choice(cells_i, size=max_cells, replace=False)

            # Solve for cross-talk
            x = self.solve_crosstalk(cells_i, added_col, c)
            res.append(x)
        res = np.vstack(res)
        self.res = pd.DataFrame(res, index=cols_i, columns=['m', 'b', 'N', 'score'])
        self.make_results()

    def solve_crosstalk(self, i, in_col, out_col):
        """ Estimate the linear cross-talk from in_col to out_col """

        # a = np.ones((len(i), 2))
        # a[:, 0] = self.FCS.data[in_col].values[i]
        a = self.FCS.data[in_col].values[i]
        a.shape = (len(i), 1)

        y = self.FCS.data[out_col].values[i]
        # y.shape = (len(i), 1)

        # x, res = sp.optimize.nnls(a, y)
        # model = sk.linear_model.LinearRegression()
        model = sk.linear_model.RANSACRegressor(sk.linear_model.LinearRegression())

        model.fit(a, y)
        x = model.estimator_
        score = model.score(a, y)
        return (x.coef_[0, 0], x.intercept_[0], len(i), score)

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
