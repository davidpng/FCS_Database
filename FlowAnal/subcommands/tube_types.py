#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Handle tube type information (export, import)
"""
import logging

from FlowAnal.database.FCS_database import FCSdatabase

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('-f', '--file',
                        help="File to import/export tubeTypes [default: db/tube_types.tmp]",
                        default='db/tube_types.tmp',
                        type=str)
    parser.add_argument('-export', '--export', help='Export tube types to <file>',
                        action='store_true'),
    parser.add_argument('-load', '--load',
                        help='Import tube types from <file> overiding all existing info',
                        action='store_true'),
    parser.add_argument('-db', '--db', help='Input/output sqlite db containing Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)


def action(args):

    # Connect to database
    db = FCSdatabase(db=args.db)

    if args.export:
        print "Export tube types to %s" % args.file
        db.exportTubeTypes(**vars(args))
    elif args.load:
        print "Import tube types from %s" % args.file
        db.importTubeTypes(**vars(args))
    else:
        print "Nothing to do"
