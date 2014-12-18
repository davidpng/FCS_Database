#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Builds sqlite database with the meta information of all flow files under specified directory

"""
import logging
from os import path
import sys

from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.__init__ import package_data
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
    parser.add_argument('-tubes', '--tubes', help='List of tube types to select',
                        nargs='+', action='store',
                        default=['Hodgkins', 'Hodgkin'], type=str)
    parser.add_argument('-dates', '--daterange',
                        help='Start and end dates to bound selection of cases \
                        [Year-Month-Date Year-Month-Date]',
                        nargs=2, action='store', type=str)


def action(args):

    # Connect to database
    db = FCSdatabase(db=args.db, rebuild=False)
    log.info("Loading database input %s" % args.db)

    # Connect to database
    out_db = FCSdatabase(db=args.outdb, rebuild=True)
    log.info("Loading database output %s" % args.outdb)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    for case, case_info in q.results.items():
        for tube, relpath in case_info.items():
            log.info("Case: %s, Tube: %s, File: %s" % (case, tube, relpath))
            filepath = path.join(args.dir, relpath)
            fFCS = FCS(filepath=filepath, import_dataframe=True)

            if fFCS.empty is False:
                try:
                    fFCS.meta_to_db(db=out_db, dir=args.dir, add_lists=True)
                    fFCS.comp_scale_FCS_data(compensation_file=comp_file,
                                             gate_coords=coords,
                                             strict=False, auto_comp=False)
                    fFCS.extract_FCS_histostats()
                    fFCS.histostats_to_db(db=out_db)
                except ValueError, e:
                    print "Skipping FCS %s because of ValueError: %s" % (filepath, e)
                except:
                    print "Skipping FCS %s because of unknown error related to: %s" % \
                        (filepath, sys.exc_info()[0])

