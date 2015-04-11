#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Builds sqlite database with the meta information of all flow files from specified file list

"""
import logging
import sys
from multiprocessing import Pool

from FlowAnal.Find_Clinical_FCS_Files import Find_Clinical_FCS_Files
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from __init__ import add_multiprocess_args

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Directory with Flow FCS files',
                        type=str)
    parser.add_argument('file_list',
                        help='Filelist of FCS files', type=str)
    parser.add_argument('-db', '--db_filepath', help='Output sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    add_multiprocess_args(parser)


def worker(x):
    res = []
    for case_tube_idx, f in x:
        try:
            fFCS = FCS(filepath=f, case_tube_idx=case_tube_idx)
            res.append((case_tube_idx, fFCS))
        except:
            print "Skipping FCS %s because of unknown error related to: %s" % \
                (f, sys.exc_info()[0])

    return res


def action(args):
    # Collect files/dirs
    Finder = Find_Clinical_FCS_Files(Filelist_Path=args.file_list)
    if args.n is not None:
        Finder.filenames = Finder.filenames[args.n]

    # Connect to database (and rebuild)
    db = FCSdatabase(db=args.db_filepath, rebuild=True)
    print "Building database %s" % db.db_file

    # Sublists
    q_list = [(case_tube_idx, f)
              for case_tube_idx, f in enumerate(Finder.filenames)]
    sublists = [q_list[i:(i + args.worker_load)]
                for i in range(0, len(q_list), args.worker_load)]

    # Process files/dirs
    p = Pool(args.workers)
    results = [p.apply_async(worker, args=(x, ))
               for x in sublists]
    p.close()

    for res in results:
        for case_tube_idx, fFCS in res.get():
            try:
                fFCS.meta_to_db(db=db, dir=args.dir, add_lists=True)
            except:
                print "Skipping FCS %s because of unknown error related to: %s" % \
                    (f, sys.exc_info()[0])
            print("{:6d} Cases processed\r".format(case_tube_idx)),
