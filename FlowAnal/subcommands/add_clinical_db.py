#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Add LISdb csv to db
"""
import logging
import shutil
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.LIS_table import LIS_table
from FlowAnal.HP_lab_table import HP_table
from FlowAnal.Cyto_table import Cyto_table

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('--lis-file', '-lis', dest='lis_file',
                        help='CSV table created from LIS db', type=str)
    parser.add_argument('--hpdb-file', '-hpdb', dest='hpdb_file',
                        help='CSV table created from hematopathology database', type=str)
    parser.add_argument('--aml-cyto', '-cyto', dest='aml_cyto', type=str,
                        help='AML Cytogenetics table')
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
        log.info('Adding clinical information from db {} to db {}'.format(args.db, args.outdb))
    else:
        args.outdb = args.db
        log.info('Adding clinical information to db {}'.format(args.outdb))

    # Open database
    outdb = FCSdatabase(db=args.outdb, rebuild=False)

    if args.lis_file is not None:
        # Load hemepath data
        a = LIS_table(db=outdb, file=args.lis_file)
        a.push_to_db()

    if args.hpdb_file is not None:
        # Load hemepath data
        a = HP_table(db=outdb, file=args.hpdb_file)
        a.push_to_db()

    if args.aml_cyto is not None:
        # Load AML Cytogenetics table
        a = Cyto_table(db=outdb, file=args.aml_cyto)
        a.push_to_db()

    outdb.close()
