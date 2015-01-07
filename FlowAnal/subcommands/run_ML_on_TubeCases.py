#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Template script for selecting a set of .fcs files and operating on them one-by-one

NOTE: There are some files that are not found because of discordance of filename \
and filename internal to .fcs file (meta info)
"""
import logging

from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.HDF5_IO import HDF5_IO
from FlowAnal.Analysis_Variables import gate_coords, comp_file, test_fcs_fn
from __init__ import add_filter_args

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('-db', '--db', help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-hdf5', '--feature-hdf5', help='Input hdf5 filepath for FCS features \
    [default: db/fcs_features.hdf5]',
                        dest='hdf5_fp', default="db/fcs_features.hdf5", type=str)
    parser.add_argument('-method', '--feature-extration-method',
                        help='The method to use to extract features [default: Full]',
                        default='Full', type=str, dest='feature_extraction_method')
    add_filter_args(parser)


def action(args):

    if args.tubes is None:
        raise ValueError('Tube types must be selected using option --tubes <>')

    # Connect to database
    db = FCSdatabase(db=args.db, rebuild=False)

    # Get case_tube_idx list [in numeric order]
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))
    case_tube_list = []
    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            log.info("Case: %s, Case_tube_idx: %s, File: %s" % (case, case_tube_idx, relpath))
            case_tube_list.append(case_tube_idx)
    case_tube_list.sort()

    # Get features
    HDF_obj = HDF5_IO(filepath=args.hdf5_fp, clobber=False)
    features_df = HDF_obj.make_single_tube_analysis(case_tube_list)
    log.debug(features_df.head())

    # Get annotations [ordered by case_tube_idx]
    annotation_df = db.query(exporttype='df', getCaseAnnotations=True, **vars(args)).results
    log.debug(annotation_df.head())
