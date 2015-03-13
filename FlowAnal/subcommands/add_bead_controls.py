#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Builds sqlite database with the meta information of all flow files under specified directory

@author: Daniel Herman MD, PhD
"""
__author__ = "Daniel Herman, MD"
__copyright__ = "Copyright 2014, Daniel Herman"
__license__ = "GPL v3"
__version__ = "1.0"
__maintainer__ = "Daniel Herman"
__email__ = "hermands@uw.edu"
__status__ = "Production"

import logging
import os
import pandas as pd
import numpy as np
import fnmatch
import datetime

from FlowAnal.database.FCS_database import FCSdatabase
log = logging.getLogger(__name__)

from FlowAnal.QC_subroutines.Load_bead_data import load_beadQC_from_csv


def build_parser(parser):
    parser.add_argument('dir', help='Directory with QC bead .csv files [required]',
                        type=str)
    parser.add_argument('-db', '--db', help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-n', '--n', type=int, default=None)


def action(args):
    # Connect to database
    log.info("Loading database input %s" % args.db)
    db = FCSdatabase(db=args.db, rebuild=False)

    # Get file list
    fps = []
    sub_directories = os.listdir(args.dir)
    for sub_dirs in sub_directories:
        for dirpath, dirnames, files in os.walk(os.path.join(args.dir, sub_dirs)):
            files_filt = fnmatch.filter(files, '*.csv')
            for f in files_filt:
                fps.append(os.path.join(dirpath, f))

    bead_dfs = []
    for i, fp in enumerate(fps):
            log.debug("Files processed: {} of {}\r".format(i, len(fps))),
            fullpath = os.path.join(args.dir, fp)
            try:
                a = load_beadQC_from_csv(fullpath)
                if a.bead_type == '8peaks':
                    bead_dfs.append(a.df)
            except Exception as ex:
                log.info('Exception [{}]: FP {} failed because of {}'.format(ex.__class__,
                                                                             fp, ex.message))
            if args.n is not None and i > args.n:
                break

    bead_df = pd.concat(bead_dfs)
    bead_df.reset_index(inplace=True, drop=True)

    def pop2fluo(x):
        y = x.split('-')
        if len(y) == 2:
            return y[0]
        else:
            return '-'.join(y[0:(len(y)-1)])

    bead_df.Populations = bead_df.Populations.apply(pop2fluo)
    bead_df.set_index(['Populations', 'cyt', 'date'], inplace=True)
    bead_df = bead_df.stack()
    bead_df.index.rename(['Fluorophore', 'cytnum', 'date', 'peak'], inplace=True)
    bead_df.name = 'MFI'
    bead_df = bead_df.reset_index()
    bead_df['date'] = pd.DatetimeIndex(bead_df.date).date.astype(str)   # Gave up because dates are too hard
    db.add_df(df=bead_df, table='Beads8peaks')
