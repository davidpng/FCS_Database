#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Template script for selecting a set of .fcs files and operating on them one-by-one

NOTE: There are some files that are not found because of discordance of filename \
and filename internal to .fcs file (meta info)
"""
import logging
from os import path

from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.FCS import FCS
from __init__ import add_filter_args

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Base directory containing .fcs files',
                        type=str)
    parser.add_argument('-db', '--db', help='Input sqlite db containing flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    add_filter_args(parser)


def action(args):
    # Connect to database
    db = FCSdatabase(db=args.db, rebuild=False)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            log.info("Case: %s, Case_tube_idx: %s, File: %s" % (case, case_tube_idx, relpath))
            filepath = path.join(args.dir, relpath)
            a = FCS(filepath=filepath)


        #     print a.empty
        #     print a.filepath
        #     print a.date
        #     print a.case_number
        #     print a.case_tube

