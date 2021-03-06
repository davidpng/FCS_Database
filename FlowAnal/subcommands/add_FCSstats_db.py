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

from FlowAnal.Analysis_Variables import gate_coords, comp_file
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from __init__ import add_filter_args

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
    parser.add_argument('--nosinglet', help='Turn off the singlet gate', action='store_true',
                        default=False)
    parser.add_argument('--noviability', help='Turn off the singlet gate', action='store_true',
                        default=False)
    parser.add_argument('-n', '--n', help='Limit to n files (for testing)', default=None,
                        type=int)
    add_filter_args(parser)


def action(args):

    # Connect to database
    log.info("Loading database input %s" % args.db)
    db = FCSdatabase(db=args.db, rebuild=False)

    # Copy database to out database
    shutil.copyfile(args.db, args.outdb)
    out_db = FCSdatabase(db=args.outdb, rebuild=False)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    n = 0
    done = False
    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            log.info("Case: %s, Case_tube_idx: %s, File: %s" % (case, case_tube_idx, relpath))
            filepath = path.join(args.dir, relpath)
            fFCS = FCS(filepath=filepath, case_tube_idx=case_tube_idx, import_dataframe=True)

            try:
                fFCS.comp_scale_FCS_data(compensation_file=comp_file,
                                         gate_coords=gate_coords,
                                         strict=False, auto_comp=False, **vars(args))
                fFCS.extract_FCS_histostats()
            except:
                fFCS.flag = 'stats_extraction_fail'
                fFCS.error_message = str(sys.exc_info()[0])

            fFCS.histostats_to_db(db=out_db)

            n += 1
            if args.n is not None and n >= args.n:
                done = True
                break
        if done is True:
            break
