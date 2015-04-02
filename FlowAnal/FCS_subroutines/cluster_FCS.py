#  from rpy2.robjects.packages import importr
import rpy2.robjects as ro
import pandas.rpy.common as com
import numpy as np

import logging
log = logging.getLogger(__name__)
import string


class cluster_FCS(object):

    def __init__(self, FCS, cluster_method='flowPeaks', **kwargs):

        self.FCS = FCS

        if cluster_method == 'flowPeaks':
            self.run_flowPeaks(**kwargs)

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
