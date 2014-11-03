#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Script to query FCS_database
"""
import logging
import pprint

from FlowAnal.database.FCS_database import FCSdatabase

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('-tubes', '--tubes', help='List of tubes to select',
                        nargs='+', action='store',
                        default=['Hodgkins'], type=str)
    parser.add_argument('-dates', '--daterange', help='Start and end dates to bound selection of cases [Year-Month-Date Year-Month-Date]',
                        nargs=2, action='store', type=str)
    parser.add_argument('-db', '--db', help='Sqlite db for Flow meta data [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-o', '--outfile', help='File to export query to',
                        default=None, type=str, dest='out_file')
    parser.add_argument("-gf", "--getfiles", action="store_true",
                        help="Query database to get .fcs files")
    parser.add_argument("-etype", "--exporttype", action="store",
                        help="Specify whether to capture dict_dict or pandas dataframe. \
                        Will force df if --outfile <X>",
                        default="dict_dict", choices=['dict_dict', 'df'])


def action(args):
    # Connect to database
    db = FCSdatabase(db=args.db)

    # Create query
    q = db.query(**vars(args))

    if args.out_file is None:
        pprint.pprint(q.results)

