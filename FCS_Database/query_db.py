#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to query FCS_database
"""
import sys
import argparse
import logging
import pprint

from database.FCS_database import FCSdatabase

log = logging.getLogger(__name__)

# Capture arguments
parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('-tubes', '--tubes', help='List of tubes to select',
                    nargs='+', action='store',
                    default=['Hodgkins'], type=str)
parser.add_argument('-db', '--db', help='Sqlite db for Flow meta data',
                    default="db/fcs.db", type=str)
parser.add_argument('-outfile', '--outfile', help='File to export query to',
                    default=None, type=str, dest='out_file')
parser.add_argument("-v", "--verbose", dest="verbose_count",
                    action="count", default=0,
                    help="increases log verbosity for each occurence.")
parser.add_argument("-getfiles", "--getfiles", action="store_true")
parser.add_argument("-exporttype", "--exporttype", action="store",
                    help="Specify whether to capture dict_dict or pandas dataframe. Will force df if --outfile <X>",
                    default="dict_dict", choices=['dict_dict', 'df'])
args = parser.parse_args(sys.argv[1:])
log.setLevel(max(3 - args.verbose_count, 0) * 10)

# Connect to database
db = FCSdatabase(db=args.db)

# Create query
q = db.query(**vars(args))

if args.out_file is None:
    pprint.pprint(q.results)

