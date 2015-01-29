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

from FlowAnal.Analysis_Variables import gate_coords, comp_file
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from __init__ import add_filter_args

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Directory with Flow FCS files [required]',
                        type=str)
    parser.add_argument('-db', '--db', help='Input sqlite3 db for Flow meta data \
    [default: fcs_meta.db]',
                        default="fcs_meta.db", type=str)
    parser.add_argument('--comp_flag',
                        help='Comp Mode', 
                        default='table',
                        type=str)
    parser.add_argument('--singlet_flag', 
                        help='Singlet gate mode',
                        default='Auto',
                        type=str)
    parser.add_argument('--viable_flag',       
                        help='Viablity gate mode', 
                        default="Fixed",
                        type=str)
    add_filter_args(parser)

def action(args):

    # Connect to database
    log.info("Loading database input %s" % args.db)
    db = FCSdatabase(db=args.db, rebuild=False)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    n = 0
    done = False
    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            log.info("Case: %s, Case_tube_idx: %s, File: %s" % (case, case_tube_idx, relpath))
            filepath = path.join(args.dir, relpath)
            fFCS = FCS(filepath=filepath, case_tube_idx=case_tube_idx, import_dataframe=True)

            try:
                fFCS.comp_scale_FCS_data(compensation_file=comp_file,gate_coords=gate_coords,
                              strict=False, rescale_lim=(-0.5,1.0),
                              classes=5,singlet_verbose=True,
                              **vars(args))
                
            except:
                log.debug("Comp Scale failed")
                fFCS.flag = 'stats_extraction_fail'
                fFCS.error_message = str(sys.exc_info()[0])

