#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Builds sqlite database of the meta information of all flow files under directory

"""
import logging

from FCS_Database.Find_Clinical_FCS_Files import Find_Clinical_FCS_Files
from FCS_Database.FCS import FCS
from FCS_Database.database.FCS_database import FCSdatabase
from FCS_Database.__init__ import __version__

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Directory with Flow FCS files [required]',
                        type=str)
    parser.add_argument('-db', '--db', help='Sqlite db for Flow meta data [default: db/fcs.db]',
                        default="db/fcs.db", type=str)


def action(args):
        # Collect files/dirs
        Finder = Find_Clinical_FCS_Files(args.dir)

        # Connect to database (and rebuild)
        db = FCSdatabase(db=args.db, rebuild=True)
        print "Building database %s" % args.db

        # Process files/dirs
        for f in Finder.filenames:
                fFCS = FCS(filepath=f, version=__version__)
                fFCS.meta_to_db(db=db, dir=args.dir, add_lists=True)

