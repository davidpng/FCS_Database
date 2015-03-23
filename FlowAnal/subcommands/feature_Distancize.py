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


def calc_emds(a, df):
    return a.calc_emds(df)


def action(args):
    # Get data
    HDF_dat = MergedFeatures_IO(filepath=args.ml_hdf5_fp, clobber=False)

    feature_df, annot_df, missing_df = HDF_dat.get_all()

    params = np.unique(zip(*feature_df.columns.values)[0])

    a = Flow_Comparison2D(shape=(10, 10))

    p = Pool(args.workers)
    results = [p.apply_async(calc_emds, args=(a, feature_df[x]))
               for x in params]
    p.close()

    for i, r in enumerate(results):
        r.get().to_hdf(args.ml_hdf5_fp, '/distance/{}/'.format(params[i]))
        log.info('Finished {} [{} of {}]\r'.format(params[i], i+1, len(params))),
