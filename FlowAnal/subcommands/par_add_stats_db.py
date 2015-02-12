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

from FlowAnal.Analysis_Variables import gate_coords, comp_file
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from __init__ import add_filter_args, add_process_args

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Directory with Flow FCS files [required]',
                        type=str)
    parser.add_argument('-db', '--db', help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-outdb', '--outdb', help='Output sqlite3 db for Flow meta data \
    [default: db/fcs_stats.db]',
                        default="db/fcs_stats.db", type=str)
    parser.add_argument('-w', '--workers', help='Number of workers [default 32]',
                        default=32, type=int)
    parser.add_argument('-l', '--load', help='Number of .fcs files to process as group,  \
    dependent on main memory size [default 600]',
                        default=600, type=int)
    parser.add_argument('-t', '--testing', help='Testing: run one load of workers',
                        default=False, action='store_true')
    add_process_args(parser)
    add_filter_args(parser)


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
        fFCS.clear_FCS_cache()
    except:
        fFCS.flag = 'stats_extraction_fail'
        fFCS.error_message = str(sys.exc_info()[0])

    return fFCS


def action(args):

    # Connect to database
    log.info("Loading database input %s" % args.db)
    db = FCSdatabase(db=args.db, rebuild=False)

    # Copy database to out database
    shutil.copyfile(args.db, args.outdb)
    out_db = FCSdatabase(db=args.outdb, rebuild=False)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    q_list = []
    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            q_list.append((path.join(args.dir, relpath), case_tube_idx))

    log.info("Length of q_list is {}".format(len(q_list)))

    # Setup lists
    n = args.load  # length of sublists
    sublists = [q_list[i:i+n] for i in range(0, len(q_list), n)]
    log.info("Number of sublists to process: {}".format(len(sublists)))

    # Setup args
    vargs = {key: value for key, value in vars(args).items()
             if key in ['viable_flag', 'singlet_flag', 'comp_flag']}

    i = 0
    for sublist in sublists:
        p = Pool(args.workers)
        results = [p.apply_async(worker, args=(case_info, ), kwds=vargs)
                   for case_info in sublist]
        p.close()

        for f in results:
            i += 1
            fFCS = f.get()
            fFCS.histostats_to_db(db=out_db)
            del fFCS
            print "Case_tubes: {} of {} have been processed\r".format(i, len(q_list)),
        del results

        if args.testing is True:
            break  # run loop once then break if testing
