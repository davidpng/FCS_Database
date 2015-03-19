#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Load hemepath db (from db or, if specified, from file) and do something with it

"""
import logging
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.HP_lab_table import HP_table

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('-file', help='CSV table created from hemepath db', type=str,
                        default=None)
    parser.add_argument('-db', '--db',
                        help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)


def action(args):

    # Open database
    db = FCSdatabase(db=args.db, rebuild=False)

    # Load hemepath data
    a = HP_table(db=db, file=args.file)

    print a.dat.head()

    db.close()
