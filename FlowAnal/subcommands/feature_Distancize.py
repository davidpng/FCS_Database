#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Template script for selecting a set of .fcs files and operating on them one-by-one

NOTE: There are some files that are not found because of discordance of filename \
and filename internal to .fcs file (meta info)
"""
import logging
import numpy as np

from FlowAnal.MergedFeatures_IO import MergedFeatures_IO
from FlowAnal.QC_subroutines.Flow_Comparison import Flow_Comparison2D

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('-ml-hdf5', '--ml-hdf5',
                        help='Input hdf5 filepath for FCS features \
    [default: db/ML_input.hdf5]',
                        dest='ml_hdf5_fp', default="db/ML_input.hdf5", type=str)


def action(args):

    # Get data
    HDF_dat = MergedFeatures_IO(filepath=args.ml_hdf5_fp, clobber=False)

    feature_df, annot_df, missing_df = HDF_dat.get_all()

    params = np.unique(zip(*feature_df.columns.values)[0])

    a = Flow_Comparison2D(shape=(10, 10))

    for p in params:
        df = feature_df[p]
        df_emds = a.calc_emds(df)
        print df_emds.iloc[0:50, :]

        # Store this somewhere (perhaps back in the same MergedFeatures_IO)
        # Could add to schema and have a list of distance matrices

        quit()
    print params
    quit()
    for p in feature_df.columns:
        print p
