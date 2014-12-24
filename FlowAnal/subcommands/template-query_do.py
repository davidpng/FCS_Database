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

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Base directory containing .fcs files',
                        type=str)
    parser.add_argument('-tubes', '--tubes', help='List of tube types to select',
                        nargs='+', action='store',
                        default=None, type=str)
    parser.add_argument('-dates', '--daterange',
                        help='Start and end dates to bound selection of cases \
                        [Year-Month-Date Year-Month-Date]',
                        nargs=2, action='store', type=str)
    parser.add_argument('-db', '--db', help='Input sqlite db containing flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)


def action(args):
    # Connect to database
    db = FCSdatabase(db=args.db, rebuild=False)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    for case, case_info in q.results.items():
        for tube, relpath in case_info.items():
            log.info("Case: %s, Tube: %s, File: %s" % (case, tube, relpath))
            filepath = path.join(args.dir, relpath)
            a = FCS(filepath=filepath)

            # DO SOMETHING
            if a.empty is False:
                print a.empty
                print a.filepath
                print a.date
                print a.case_number
                print a.case_tube

