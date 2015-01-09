#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Builds sqlite database with the meta information of all flow files from specified file list

"""
import logging
from FlowAnal.Find_Clinical_FCS_Files import Find_Clinical_FCS_Files
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Directory with Flow FCS files [required]',
                        type=str)
    parser.add_argument('-fl', '--file_list', help='Filelist of FCS files\
    [default: db/FoundFile.txt] [required]', default='db/FoundFile.txt', type=str)
    parser.add_argument('-db', '--db_filepath', help='Output sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)


def action(args):

    # Collect files/dirs
    Finder = Find_Clinical_FCS_Files(Filelist_Path=args.file_list)

    # Connect to database (and rebuild)
    db = FCSdatabase(db=args.db_filepath, rebuild=True)
    print "Building database %s" % db.db_file

    # Process files/dirs
    case_tube_idx = 0
    for f in Finder.filenames:

        fFCS = FCS(filepath=f, case_tube_idx=case_tube_idx)
        fFCS.meta_to_db(db=db, dir=args.dir, add_lists=True)
        print("{:6d} Cases uploaded\r".format(case_tube_idx)),

        case_tube_idx += 1
