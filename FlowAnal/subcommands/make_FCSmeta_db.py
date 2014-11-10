#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Builds sqlite database with the meta information of all flow files under specified directory

"""
import logging
import os
from FlowAnal.Find_Clinical_FCS_Files import Find_Clinical_FCS_Files
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Directory with Flow FCS files [required]',
                        type=str)
    parser.add_argument('-db', '--db', help='Output sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-fl', '--fl',help='Output filelist of found FCS files\
    [default: db/FoundFile.txt]', default='db/FoundFile.txt', type=str)
    

def action(args):
    # Collect files/dirs
    Finder = Find_Clinical_FCS_Files(args.dir,Filelist_Path=args.fl)

    # Connect to database (and rebuild)
    db = FCSdatabase(db=args.db, rebuild=True)
    print "Building database %s" % args.db

    # Process files/dirs
    for f in Finder.filenames:
        fFCS = FCS(filepath=f)
        fFCS.meta_to_db(db=db, dir=args.dir, add_lists=True)




