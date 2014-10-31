#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to query FCS_database
"""
import sys
import argparse
import logging

from database.FCS_database import FCSdatabase

log = logging.getLogger(__name__)

# Capture arguments
parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('-export', '--export', help='Export tube types to data/tube_types.tmp',
                    action='store_true'),
parser.add_argument('-load', '--load', help='Import tube types',
                    action='store_true'),
parser.add_argument('-db', '--db', help='Sqlite db for Flow meta data',
                    default="db/fcs.db", type=str)
parser.add_argument('-file', '--file', help='File to import/export tubeTypes', default=None,
                    type=str)
parser.add_argument("-v", "--verbose", dest="verbose_count",
                    action="count", default=0,
                    help="increases log verbosity for each occurence.")
args = parser.parse_args(sys.argv[1:])
log.setLevel(max(3 - args.verbose_count, 0) * 10)

# Connect to database
db = FCSdatabase(db=args.db)

if args.export:
    db.exportTubeTypes(**vars(args))
elif args.load:
    db.importTubeTypes(**vars(args))

