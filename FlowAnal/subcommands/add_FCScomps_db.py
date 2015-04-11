#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Builds sqlite database with the meta information of all flow files under specified directory

@author: Daniel Herman MD, PhD
"""
__author__ = "Daniel Herman, MD"
__copyright__ = "Copyright 2014, Daniel Herman"
__license__ = "GPL v3"
__version__ = "1.0"
__maintainer__ = "Daniel Herman"
__email__ = "hermands@uw.edu"
__status__ = "Production"

import logging
from os import path
import shutil
from multiprocessing import Pool

from FlowAnal.Find_Clinical_FCS_Files import Find_Clinical_FCS_Files
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.FCS_subroutines.Process_Single_Antigen import Process_Single_Antigen
from __init__ import add_multiprocess_args
log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Directory with Comp FCS files [required]',
                        type=str)
    parser.add_argument('-db', '--db', help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-outdb', '--outdb', help='Output sqlite3 db for Flow meta data \
    [default: db/fcs_stats.db]',
                        default=None, type=str)
    parser.add_argument('-exclude', '--ex', help='List of directories to exclude',
                        default=[".."], nargs='+', type=str)
    parser.add_argument('-file', '--fcs-file', help='Single file to process',
                        default=None, type=str)
    add_multiprocess_args(parser)


def worker(x, **kwargs):
    filepath = path.join(kwargs['dir'], x[1])
    log.debug("Comp_tube_idx: %s, File: %s" % (x[0], x[1]))
    fFCS = FCS(ftype='comp',
               filepath=filepath,
               comp_tube_idx=x[0],
               import_dataframe=True)

    if fFCS.empty is False:
        a = Process_Single_Antigen(fFCS)
        try:
            a.Calculate_Comp()
        except Exception, e:
            a.flag = 'Could not fit'
            a.error_message = str(e)

    del(fFCS)
    del(a.FCS)
    return a


def action(args):
    # Connect to database
    log.info("Loading database input %s" % args.db)
    db = FCSdatabase(db=args.db, rebuild=False)

    if args.outdb is not None:
        # Copy database to out database
        shutil.copyfile(args.db, args.outdb)
        out_db = FCSdatabase(db=args.outdb, rebuild=False)
    else:
        out_db = db

    # Find files
    if args.fcs_file is None:
        comp_files = Find_Clinical_FCS_Files(args.dir,
                                             pattern='*.fcs',
                                             exclude=args.ex,
                                             **vars(args)).filenames
        if args.n is not None:
            comp_files = comp_files[args.n]
    else:
        comp_files = [args.fcs_file]
    comp_files = zip(range(comp_files), comp_files)

    # Setup lists
    sublists = [comp_files[i:(i + args.load)]
                for i in range(0, len(comp_files), args.load)]
    log.info("Number of sublists to process: {}".format(len(sublists)))

    vargs = {'dir': args.dir}

    i = 0
    for sublist in sublists:
        p = Pool(args.workers)
        results = [p.apply_async(worker, args=(case_info, ), kwds=vargs)
                   for case_info in sublist]
        p.close()

        for f in results:
            i += 1
            a = f.get()
            a.push_db(out_db)
            del a
            print "Case_tubes: {} of {} have been processed\r".format(i, len(comp_files)),
        del results
