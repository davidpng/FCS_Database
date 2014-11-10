#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Builds sqlite database with the meta information of all flow files under specified directory

"""
import logging

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


def action(args):
        # Collect files/dirs
        Finder = Find_Clinical_FCS_Files(args.dir)

        # Connect to database (and rebuild)
        db = FCSdatabase(db=args.db, rebuild=True)
        print "Building database %s" % args.db

        # Process files/dirs
        for f in Finder.filenames:
            fFCS = FCS(filepath=f, import_dataframe=True)
            fFCS.meta_to_db(db=db, dir=args.dir, add_lists=True)

            fFCS.extract_FCS_histostats()
            fFCS.histostats_to_db(db=db)




