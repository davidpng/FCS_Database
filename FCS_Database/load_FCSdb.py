#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 20 13:56:55 2014

@author: ngdavid
"""
import sys
import argparse
import logging

from FCS_Database.HEADER_Find_FCS_files import Find_Clinical_FCS_Files
from FCS import FCS
from database.FCS_database import FCSdatabase

import pprint
log = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)

# Capture arguments
parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('-dir', '--dir', help='Directory with Flow FCS files',
                    default="$HOME/Desktop/Ubuntu_Dropbox/Myeloid_Data/Myeloid", type=str)
parser.add_argument('-db', '--db', help='Sqlite db for Flow meta data',
                    default="db/fcs.db", type=str)
parser.add_argument('-rebuilddb', '--rebuilddb', help='Drop db and rebuild',
                    action="store_true")
parser.add_argument("-v", "--verbose", dest="verbose_count",
                    action="count", default=0,
                    help="increases log verbosity for each occurence.")
args = parser.parse_args(sys.argv[1:])
log.setLevel(max(3 - args.verbose_count, 0) * 10)

# Collect files/dirs
Finder = Find_Clinical_FCS_Files(args.dir)

# Connect to database (and rebuild if --rebuilddb)
db = FCSdatabase(db=args.db, rebuild=args.rebuilddb)

# Process files/dirs
for f in Finder.filenames:
        fFCS = FCS(filepath=f)
        fFCS.meta_to_db(db=db, dir=args.dir, add_lists=True)
