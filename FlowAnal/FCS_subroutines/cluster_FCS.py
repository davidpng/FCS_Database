import rpy2.robjects as ro
from rpy2.robjects.packages import importr
import pandas.rpy.common as com
import numpy as np
import os

import logging
log = logging.getLogger(__name__)
import string

priors = {'lymphs': (5.5e4, 6.5e4),
          'myeloid': (1.15e4, 1.5e5)}


class cluster_FCS(object):

    def __init__(self, FCS, cluster_method='flowPeaks', **kwargs):

        self.FCS = FCS
        self.filepath = FCS.filepath

        if cluster_method == 'flowPeaks':
            self.run_flowPeaks(**kwargs)
        elif cluster_method == 'comp_gate':
            self.Comp_Gate(fp=self.filepath,
                           **kwargs)
        elif cluster_method == 'lymph_gate':
            self.Lymph_Gate(fp=self.filepath,
                            **kwargs)

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

    def Comp_Gate(self, fp, min_clust_N=200, **kwargs):

        log.info('Gating for comp calc')
        flowCore = importr('flowCore')
        flowStats = importr('flowStats')
        flowClust = importr('flowClust')
        openCyto = importr('openCyto')
        # importr('parallel')

        a = flowCore.read_FCS(fp)

        # Viability
        f_vb = openCyto.mindensity(a, channel='FSC-A',
                                   gate_range=ro.IntVector((0, 7e4)))
        a_vb = flowCore.Subset(a, f_vb)
        gate_vb = flowCore.filter(a, f_vb)
        gate_vb = np.asarray(gate_vb.do_slot('subSet'), dtype=bool)

        # Singlet
        f_sg = flowStats.singletGate(a_vb, area="FSC-A", height="FSC-H",
                                     wider_gate=True, maxit=20,
                                     prediction_level=0.9999)
        a_sg = flowCore.Subset(a_vb, f_sg)
        gate_sg = flowCore.filter(a, f_sg)
        gate_sg = np.asarray(gate_sg.do_slot('subSet'), dtype=bool)

        # Pop cluster
        res = flowClust.flowClust(a_sg, varNames=ro.StrVector(("SSC-H", "FSC-A")),
                                  K=ro.IntVector(range(1, 11)), B=100, level=0.75,
                                  z_cutoff=0.6)

        # pick cluster
        x = np.asarray(flowClust.criterion(res, "BIC"))
        x = x - min(x)
        x = x / max(x)
        y = x[1:len(x)] - x[0:(len(x)-1)]
        if len(x) == 0:
            raise "Cluster found only {} clusters".format(len(x))
        elif len(x) == 1:
            nc = 0
        else:
            tmp = np.where(y < 0.03)[0]
            if len(tmp) == 0:
                nc = len(res) - 1
            else:
                nc = max(tmp[0] + 1,
                         1)
        res = res[nc]

        cluster = np.asarray(flowClust.Map(res))
        cluster[cluster < 0] = 0
        clusters_to_elim = np.where(np.bincount(cluster, minlength=nc+1) < min_clust_N)[0]
        cluster[np.in1d(cluster, clusters_to_elim) | (cluster == 0)] = -1

        # Climb back to original
        cluster2 = np.empty(shape=len(gate_sg), dtype=np.int)
        cluster2.fill(-2)
        cluster2[gate_vb & gate_sg] = cluster
        self.FCS.cluster = cluster2

    def Lymph_Gate(self, fp, min_clust_N=200, **kwargs):

        log.info('Gating for Lymph gate')
        flowCore = importr('flowCore')
        flowStats = importr('flowStats')
        openCyto = importr('openCyto')
        flowClust = importr('flowClust')

        a = flowCore.read_FCS(fp)

        # Viability
        f_vb = openCyto.mindensity(a, channel='FSC-A',
                                   gate_range=ro.IntVector((0, 7e4)))
        a_vb = flowCore.Subset(a, f_vb)
        gate_vb = flowCore.filter(a, f_vb)
        gate_vb = np.asarray(gate_vb.do_slot('subSet'), dtype=bool)

        # Singlet
        f_sg = flowStats.singletGate(a_vb, area="FSC-A", height="FSC-H",
                                     wider_gate=True, maxit=20,
                                     prediction_level=0.9999)
        a_sg = flowCore.Subset(a_vb, f_sg)
        gate_sg = flowCore.filter(a, f_sg)
        gate_sg = np.asarray(gate_sg.do_slot('subSet'), dtype=bool)

        # Pop cluster
        f_lymph = flowCore.rectangleGate(filterId="lymph_gate",
                                         _gate=ro.ListVector({'SSC-H': ro.IntVector((0, 1.1e4)),
                                                              'FSC-A': ro.IntVector((5e4,
                                                                                     1.3e5))}))
        a_lymph = flowCore.Subset(a_sg, f_lymph)
        gate_lymph = flowCore.filter(a, f_lymph)
        gate_lymph = np.asarray(gate_lymph.do_slot('subSet'), dtype=bool)

        # Climb back to original
        cluster2 = np.empty(shape=len(gate_sg), dtype=np.int)
        cluster2.fill(-1)
        cluster2[gate_vb & gate_sg & gate_lymph] = 1
        self.FCS.cluster = cluster2
