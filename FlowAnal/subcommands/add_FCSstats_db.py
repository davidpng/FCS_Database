#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Builds sqlite database with the meta information of all flow files under specified directory

"""
import logging
from os import path
import sys
from sqlalchemy.exc import IntegrityError

from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.__init__ import package_data
from __init__ import add_filter_args

log = logging.getLogger(__name__)

coords = {'singlet': [(0.01, 0.06), (0.60, 0.75), (0.93, 0.977), (0.988, 0.86),
                      (0.456, 0.379), (0.05, 0.0), (0.0, 0.0)],
          'viable': [(0.358, 0.174), (0.609, 0.241), (0.822, 0.132), (0.989, 0.298),
                     (1.0, 1.0), (0.5, 1.0), (0.358, 0.174)]}

comp_file = {'1': package_data('Spectral_Overlap_Lib_LSRA.txt'),
             '2': package_data('Spectral_Overlap_Lib_LSRB.txt'),
             '3': package_data('Spectral_Overlap_Lib_LSRB.txt')}


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


def action(args):

    # Connect to database
    log.info("Loading database input %s" % args.db)
    db = FCSdatabase(db=args.db, rebuild=False)

    # Connect to out database
    log.info("Loading database output %s" % args.outdb)
    out_db = FCSdatabase(db=args.outdb, rebuild=True)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            log.info("Case: %s, Case_tube_idx: %s, File: %s" % (case, case_tube_idx, relpath))
            filepath = path.join(args.dir, relpath)
            fFCS = FCS(filepath=filepath, import_dataframe=True)

            try:
                fFCS.meta_to_db(db=out_db, dir=args.dir, add_lists=True)
                fFCS.comp_scale_FCS_data(compensation_file=comp_file,
                                         gate_coords=coords,
                                         strict=False, auto_comp=False)
                fFCS.extract_FCS_histostats()
                fFCS.histostats_to_db(db=out_db)
            except ValueError, e:
                print "Skipping FCS %s because of ValueError: %s" % (filepath, e)
            except KeyError, e:
                print "Skipping FCS %s because of KeyError: %s" % (filepath, e)
            except IntegrityError, e:
                print "Skipping Case: %s, Tube: %s, Date: %s, filepath: %s because of IntegrityError: %s" % \
                    (case, case_tube_idx, filepath, e)
            except:
                print "Skipping FCS %s because of unknown error related to: %s" % \
                    (filepath, sys.exc_info()[0])

