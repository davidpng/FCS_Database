#  from rpy2.robjects.packages import importr
import rpy2.robjects as ro
from rpy2.robjects.packages import importr
import pandas.rpy.common as com
import numpy as np
import os

import logging
log = logging.getLogger(__name__)
import string


class cluster_FCS(object):

    def __init__(self, FCS, cluster_method='flowPeaks', **kwargs):

        self.FCS = FCS
        self.filepath = FCS.filepath

        if cluster_method == 'flowPeaks':
            self.run_flowPeaks(**kwargs)
        elif cluster_method == 'comp_gate':
            self.Comp_Gate(self.filepath, **kwargs)

    def run_flowPeaks(self, params=['FSC-A',
                                    'SSC-H',
                                    'CD45 APC-H7',
                                    'CD71 APC-A700'], **kwargs):
        log.info('Running flowPeaks')

        params = [string.replace(x, ' ', '.') for x in params]
        params = [string.replace(x, '-', '.') for x in params]

        ro.r('library(flowPeaks)')
        rdf = com.convert_to_r_dataframe(self.FCS.data)
        ro.globalenv['df'] = rdf
        cmd = 'fp <- flowPeaks(df[, c(' + \
              ','.join(["'{}'".format(p)
                        for p in params]) + ')])'
        ro.r(cmd)
        ro.r('pc <- assign.flowPeaks(fp, fp$x, tol=0.005, fc=0.5)')
        cluster = np.asarray(ro.r('pc'))
        cluster[cluster < 0] = -1
        self.FCS.cluster = cluster

    def Comp_Gate(fp, **kwargs):

        log.info('Gating for comp calc')
        flowCore = importr('flowCore')
        flowStats = importr('flowStats')
        flowClust = importr('flowClust')
        importr('parallel')

        a = flowCore.read_FCS(fp)
        f_sg = flowStats.singletGate(a, area="FSC-A", height="FSC-H",
                                     wider_gate=True, maxit=10,
                                     prediction_level=0.9999)
        a_sg = flowCore.Subset(a, f_sg)
        f_SvF = flowClust.tmixFilter('f_SvF', parameters=ro.StrVector(("SSC-H", "FSC-A")),
                                     K=ro.IntVector(range(1, 9)), B=100, level=0.95)
        f_SvF.do_slot_assign('z.cutoff', ro.FloatVector([0.6]))
        res = flowCore.filter(a_sg, f_SvF)
        x = np.asarray(flowClust.criterion(res, "BIC"))
        x = x - min(x)
        nc = np.where(x / max(x) >= 0.9)[0][0]
        cluster = np.asarray(flowClust.Map(res[nc]))
        print cluster

