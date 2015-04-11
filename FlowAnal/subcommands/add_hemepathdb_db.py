#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Add Hemepath db derived csv to sqlite db
"""
import logging
import shutil
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.HP_lab_table import HP_table

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('file', help='CSV table created from hemepath db', type=str)
    parser.add_argument('-db', '--db',
                        help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-outdb', '--outdb', help='Output sqlite3 db [default: None]',
                        default=None, type=str)


def action(args):

    # Copy database
    if args.outdb is not None:
        shutil.copyfile(args.db, args.outdb)
    else:
        args.outdb = args.db

    # Open database
    outdb = FCSdatabase(db=args.outdb, rebuild=False)

    # Load hemepath data
    a = HP_table(db=outdb, file=args.file)

    # Push hemepath data to sql db
    a.push_to_db()

    outdb.close()