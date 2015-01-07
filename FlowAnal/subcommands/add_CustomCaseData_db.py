#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Builds sqlite database from input database (meta information of all flow files) that includes
only cases specified in input <file>. Input <file> data is added to custom data table.

If option --nowhittle is specified then cases not specified in input <file> are included.

INPUT file format: tab-deliminated text with column labels <case_number> and <category>

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
    parser.add_argument('-nw', '--no-whittle', dest='no_whittle',
                        help='Keep meta data from cases not included in <file> \
                        in <outdb>', action='store_true')


def action(args):
    # Copy database
    shutil.copyfile(args.db, args.outdb)
    outdb = FCSdatabase(db=args.outdb, rebuild=False)

    # Add text table and whittle cases not in db (unless args says otherwise)
    outdb.addCustomCaseData(file=args.file, whittle=not args.no_whittle)

    if args.no_whittle is False:
        # Delete cases in db not in Custom table [do not add to exclusions table]
        outdb.query(delCasesByCustom=True)

    outdb.close()
