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
import sys
import shutil
from multiprocessing import Pool
import traceback

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
    parser.add_argument('-plot', '--plot', help='Plot out the comp info',
                        default=False, action='store_true')
    parser.add_argument('-add-gate', '--add-gate', help='Use a gate to clean up',
                        default=False, action='store_true')
    parser.add_argument('-fit', '--fit', help='Calculate compensation',
                        default=False, action='store_true')
    parser.add_argument('-model', '--model', help='Model to use for fitting',
                        default='RANSAC', type=str)
    parser.add_argument('-precluster', '--precluster', help='Precluster cluster method',
                        default=None, type=str, choices=['comp_gate'])
    add_multiprocess_args(parser)


def worker(x, **kwargs):
    filepath = path.join(kwargs['dir'], x[1])
    log.debug("Comp_tube_idx: %s, File: %s" % (x[0], x[1]))
    if kwargs['fit'] is True or kwargs['plot'] is True:
        fFCS = FCS(ftype='comp',
                   filepath=filepath,
                   comp_tube_idx=x[0],
                   import_dataframe=True)
    else:
        fFCS = FCS(ftype='comp',
                   filepath=filepath,
                   comp_tube_idx=x[0],
                   import_dataframe=False)

    if 'precluster' in kwargs:
        fFCS.make_clusters(cluster_method=kwargs['precluster'], **kwargs)
    quit()

    a = Process_Single_Antigen(fFCS, dir=kwargs['dir'])

    if a.empty is False:
        try:
            if kwargs['fit'] is True:
                a.fit_Comp()
            if kwargs['plot'] is True:
                a.plot()
        except Exception, e:
            traceback.print_exc(file=sys.stdout)
            raise
            a.flag = 'Could not fit'
            a.error_message = str(e)

    fFCS.clear_FCS_data()
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
    else:
        comp_files = [args.fcs_file]
    comp_files = zip(range(len(comp_files)), comp_files)

    # Setup lists
    sublists = [comp_files[i:(i + args.load)]
                for i in range(0, len(comp_files), args.load)]
    log.info("Number of sublists to process: {}".format(len(sublists)))

    vargs = {'dir': args.dir, 'plot': args.plot, 'add_gate': args.add_gate,
             'model': args.model, 'fit': args.fit, 'precluster': args.precluster}

    i = 0
    for sublist in sublists:
        if args.workers > 1:
            p = Pool(args.workers)
            results = [p.apply_async(worker, args=(case_info, ), kwds=vargs)
                       for case_info in sublist]
            p.close()
        else:
            results = [worker(case_info, **vargs)
                       for case_info in sublist]

        for f in results:
            if args.workers > 1:
                a = f.get()
            else:
                a = f
            if a.empty is False:
                try:
                    a.push_db(out_db)
                except Exception, e:
                    log.info('Failed to push [{}] because of [{}]'.format(a.filepath,
                                                                          str(e)))
                del a
            i += 1
            print "Case_tubes: {} of {} have been processed\r".format(i, len(comp_files)),
        del results
    print "\n"
