#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Builds sqlite database with the meta information of all flow files from specified file list

"""
import logging
import shutil
from FlowAnal.database.FCS_database import FCSdatabase

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('file', help='Tab-separated text table with Case information. \
    Columns must include <case_number> and <group>', type=str)
    parser.add_argument('-db', '--db', help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-outdb', '--outdb', help='Output sqlite3 db for Flow meta data \
    [default: db/fcs_custom.db]',
                        default="db/fcs_custom.db", type=str)
    parser.add_argument('-w', '--whittle', help='Remove all cases not included in <file> \
    from <outdb>', action='store_true')


def action(args):
    # Copy database
    shutil.copyfile(args.db, args.outdb)
    outdb = FCSdatabase(db=args.outdb, rebuild=False)

    # Add text table
    outdb.addCustomCaseData(file=args.file)

    if args.whittle is True:
        # Delete other data
        outdb.query(delCasesByCustom=True)
        outdb.close()
