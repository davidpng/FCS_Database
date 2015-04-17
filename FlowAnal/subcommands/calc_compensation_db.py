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
from os import path
import sys
import shutil
from multiprocessing import Pool
import pandas as pd
import numpy as np

from FlowAnal.Analysis_Variables import tubes
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from __init__ import add_filter_args, add_process_args, add_multiprocess_args

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Directory with Flow FCS files [required]',
                        type=str)
    parser.add_argument('-db', '--db', help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-outdb', '--outdb', help='Output sqlite3 db for Flow meta data',
                        default=None, type=str)
    add_multiprocess_args(parser)


def worker(in_list, **kwargs):
    """
    Still need to work on handling of cases that did not extract correctly
    """
    filepath = in_list[0]
    case_tube_idx = in_list[1]
    fFCS = FCS(filepath=filepath, case_tube_idx=case_tube_idx, import_dataframe=True)
    try:
        fFCS.comp_scale_FCS_data(compensation_file=comp_file,
                                 gate_coords=gate_coords,
                                 strict=False, **kwargs)
        fFCS.extract_FCS_histostats()
    except:
        fFCS.flag = 'stats_extraction_fail'
        fFCS.error_message = str(sys.exc_info()[0])

    fFCS.clear_FCS_data()
    return fFCS


def action(args):

    # Connect to database
    log.info("Loading database input %s" % args.db)
    db = FCSdatabase(db=args.db, rebuild=False)

    if args.outdb is not None:
        # Copy database to out database
        shutil.copyfile(args.db, args.outdb)
        out_db = FCSdatabase(db=args.outdb, rebuild=False)
    else:
        out_db = db

    # Create query
    df = db.query(getSingleComp=True).results
    df.drop(['xt_Channel_Number', 'm', 'b', 'N', 'score'], inplace=True, axis=1)
    df = df.loc[df.old == 'False', :]
    df.drop_duplicates(inplace=True)

    # Add tube info
    a_tubes = pd.DataFrame(tubes['Myeloid 1a'])
    df = pd.merge(df, a_tubes)
    df = df.loc[df.cytnum.isin(('1', '2')), :]
    df.sort(['date', 'cytnum', 'Channel_Number'], inplace=True)
    df.reset_index(inplace=True, drop=True)

    start_time = df.groupby(['cytnum', 'Channel_Name'])['date'].min().max()
    start_idx = df.index[df.date == start_time].values[0]

    def pick_most_recent(x, cur_time):
        a = x.loc[x.date <= cur_time, 'date']
        id = x.index[x.date == a.max()].values[0:1]
        return x.loc[id, :]

    comp_df = df.groupby(['cytnum',
                          'Channel_Name']).apply(lambda x: pick_most_recent(x,
                                                                            start_time))

    comp_df = comp_df[['cytnum', 'Channel_Number', 'comp_tube_idx']]
    comp_df['date'] = start_time
    comp_df['time_idx'] = 0
    comp_df.set_index(['time_idx', 'date', 'cytnum', 'Channel_Number'], drop=True, inplace=True)
    comp_df.sort_index(inplace=True)

    comps_df = comp_df.copy()
    for i, idx in enumerate(range(start_idx+1, df.shape[0])):
        new_row = df.loc[idx, :]
        index = comp_df.index
        index_names = index.names
        index = [(i+1, new_row.date, new_row.cytnum, x[3])
                 if x[2] == new_row.cytnum
                 else (i+1, x[1], x[2], x[3])
                 for x in index.tolist()]
        comp_df.index = pd.MultiIndex.from_tuples(index, names=index_names)
        comp_df.loc[(i+1, new_row.date, new_row.cytnum, new_row.Channel_Number),
                    'comp_tube_idx'] = new_row.comp_tube_idx
        tmp = comp_df.xs(new_row.cytnum, level='cytnum', drop_level=False)
        comps_df = comps_df.append(tmp)

    comps_df.reset_index(inplace=True, drop=False)
    comps_df = pd.merge(comps_df, df[['comp_tube_idx', 'dirname', 'filename']],
                        left_on='comp_tube_idx', right_on='comp_tube_idx')
    comps_df.sort(['time_idx', 'Channel_Number'], inplace=True)
    comps_df.to_csv('comp_test.txt', sep="\t")
