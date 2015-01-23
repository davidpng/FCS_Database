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
from sqlalchemy.exc import IntegrityError
import shutil
import multiprocessing

from FlowAnal.Analysis_Variables import gate_coords,comp_file
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.__init__ import package_data
from __init__ import add_filter_args

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
    parser.add_argument('-w', '--workers', help='Number of workers [default 4]',
                        default=4,type=int)
    parser.add_argument('-d', '--depth', help='worker load per worker [default 20]',
                        default=20,type=int)
                        
    add_filter_args(parser)

def worker(in_list):
    filepath = in_list[0]
    case_tube_index = in_list[1]
    fFCS = FCS(filepath=filepath, case_tube_idx=case_tube_idx, import_dataframe=True)
    fFCS.comp_scale_FCS_data(compensation_file=comp_file,
                             gate_coords=gate_coords,
                             strict=False, auto_comp=False)
    fFCS.extract_FCS_histostats()
    #fFCS.histostats_to_db(db=out_db)
    fFCS.clear_FCS_cache()
    print fFCS.case_number
    
def action(args):

    # Connect to database
    log.info("Loading database input %s" % args.db)
    db = FCSdatabase(db=args.db, rebuild=False)

    # Copy database to out database
    shutil.copyfile(args.db, args.outdb)
    out_db = FCSdatabase(db=args.outdb, rebuild=False)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    q_list = []
    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            q_list.append((path.join(args.dir, relpath),case_tube_idx))
        
    print("Length of q_list is {}".format(len(q_list)))
    for in_list in q_list[:3]:
        worker(in_list)
'''
            try:
                fFCS.comp_scale_FCS_data(compensation_file=comp_file,
                                         gate_coords=gate_coords,
                                         strict=False, auto_comp=False)
                fFCS.extract_FCS_histostats()
                fFCS.histostats_to_db(db=out_db)
            except ValueError, e:
                print "Skipping FCS %s because of ValueError: %s" % (filepath, e)
            except KeyError, e:
                print "Skipping FCS %s because of KeyError: %s" % (filepath, e)
            except IntegrityError, e:
                print "Skipping Case: %s, Tube: %s, filepath: %s because of IntegrityError: %s" % \
                    (case, case_tube_idx, filepath, e)
            except:
                print "Skipping FCS %s because of unknown error related to: %s" % \
                    (filepath, sys.exc_info()[0])
'''