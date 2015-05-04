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

from FlowAnal.Analysis_Variables import gate_coords, comp_file
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from __init__ import add_filter_args, add_process_args, add_multiprocess_args

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Directory with Flow FCS files [required]',
                        type=str)
    parser.add_argument('-db', '--db', help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-outdb', '--outdb', help='Output sqlite3 db for Flow meta data \
    [default: db/fcs_stats.db]',
                        default="db/fcs_stats.db", type=str)
    add_filter_args(parser)
    add_process_args(parser)
    add_multiprocess_args(parser)


def worker(in_list, **kwargs):
    """
    Still need to work on handling of cases that did not extract correctly
    """
    filepath = in_list[0]
    case_tube_idx = in_list[1]
    fFCS = FCS(filepath=filepath, case_tube_idx=case_tube_idx, import_dataframe=True)
    #    try:
    if fFCS.empty is False:
        fFCS.comp_scale_FCS_data(compensation_file=comp_file,
                                 gate_coords=gate_coords,
                                 strict=False, **kwargs)
        fFCS.make_clusters(cluster_method='lymph_gate', **kwargs)
        outfile = 'output/' + '_'.join([str(fFCS.case_tube_idx),
                                        fFCS.date.strftime("%Y%m%d"),
                                        fFCS.cytnum])

        fFCS.visualize_2D(outfile=outfile, vizmode='M1_gating', logit=True)
    # except Exception, e:
    #     fFCS.flag = 'stats_extraction_fail'
    #     fFCS.error_message = str(sys.exc_info()[0])
    #     raise Exception(e)

    fFCS.clear_FCS_data()
    return fFCS


def action(args):
    # Connect to database
    log.info("Loading database input %s" % args.db)
    db = FCSdatabase(db=args.db, rebuild=False)

    # Copy database to out database
    # shutil.copyfile(args.db, args.outdb)
    # out_db = FCSdatabase(db=args.outdb, rebuild=False)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True,
                 **vars(args))

    q_list = []
    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            q_list.append((path.join(args.dir, relpath), case_tube_idx))

    log.info("Length of q_list is {}".format(len(q_list)))

    # Setup lists
    n = args.load  # length of sublists
    sublists = [q_list[i:i+n]
                for i in range(0, len(q_list), n)]
    log.info("Number of sublists to process: {}".format(len(sublists)))

    # Setup args
    vargs = {key: value for key, value in vars(args).items()
             if key in ['viable_flag', 'singlet_flag', 'comp_flag', 'gates1d']}

    for sublist in sublists:
        if args.workers > 1:
            p = Pool(args.workers)
            results = [p.apply_async(worker, args=(case_info, ), kwds=vargs)
                       for case_info in sublist]
            p.close()
        else:
            results = [worker(case_info, **vargs)
                       for case_info in sublist]

        for i, f in enumerate(results):
            if args.workers > 1:
                fFCS = f.get()
            else:
                fFCS = f
            # fFCS.histostats_to_db(db=out_db)
            del fFCS
            print "Case_tubes: {} of {} have been processed\r".format(i, len(q_list)),
        del results
