#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Template script for selecting a set of .fcs files and operating on them one-by-one

NOTE: There are some files that are not found because of discordance of filename \
and filename internal to .fcs file (meta info)
"""
import logging
import warnings
import numpy as np
import tables
from sklearn import manifold
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from multiprocessing import Pool

from FlowAnal.MergedFeatures_IO import MergedFeatures_IO
from FlowAnal.QC_subroutines.Flow_Comparison import Flow_Comparison2D

log = logging.getLogger(__name__)
warnings.simplefilter('ignore', tables.NaturalNameWarning)


def build_parser(parser):
    parser.add_argument('-ml-hdf5', '--ml-hdf5',
                        help='Input hdf5 filepath for FCS features \
    [default: db/ML_input.hdf5]',
                        dest='ml_hdf5_fp', default="db/ML_input.hdf5", type=str)
    parser.add_argument('-workers', '--workers', type=int,
                        default=20,
                        help='Number of workers')


def action(args):
    # Get data
    HDF_dat = MergedFeatures_IO(filepath=args.ml_hdf5_fp, clobber=False)

    # Annotations
    annot = HDF_dat.get_annotations()
    annot = annot.groupby(annot.index).first()
    _, annot = np.unique(annot, return_inverse=True)

    params = HDF_dat.get_dist_groups()
    for p in params:
        mat, ctis = HDF_dat.get_dist_matrix(p)


        # seed = np.random.RandomState(seed=3)
        # mds = manifold.MDS(n_init=4, n_components=10, max_iter=3000, eps=1e-9, random_state=seed,
        #                    dissimilarity="precomputed", n_jobs=1)
        # fit = mds.fit(mat)
        # mmat = fit.embedding_
        # ve = fit.stress_

        U, s, _ = np.linalg.svd(np.dot(mat, mat.T))
        # print s/np.sum(s)

        fig = plt.figure()
        plt.axes([0., 0., 1., 1.])
        plt.scatter(U[0, :],
                    U[1, :], s=30, c=annot,
                    cmap=plt.cm.Spectral)
        fig.savefig('.'.join([p, 'png']), bbox_inches='tight')
        plt.close(fig)

    # a = Flow_Comparison2D(shape=(10, 10))

    # p = Pool(args.workers)
    # results = [p.apply_async(calc_emds, args=(a, feature_df[x]))
    #            for x in params]
    # p.close()

    # for i, r in enumerate(results):
    #     r.get().to_hdf(args.ml_hdf5_fp, '/distance/{}/'.format(params[i]))
    #     log.info('Finished {} [{} of {}]\r'.format(params[i], i+1, len(params))),
