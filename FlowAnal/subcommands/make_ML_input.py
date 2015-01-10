#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Template script for selecting a set of .fcs files and operating on them one-by-one

NOTE: There are some files that are not found because of discordance of filename \
and filename internal to .fcs file (meta info)
"""
import logging

from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.HDF5_IO import HDF5_IO
from FlowAnal.CustomData import CustomData
from __init__ import add_filter_args

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('-db', '--db', help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-feature-hdf5', '--feature-hdf5', help='Input hdf5 filepath for FCS features \
    [default: db/fcs_features.hdf5]',
                        dest='feature_hdf5_fp', default="db/fcs_features.hdf5", type=str)
    parser.add_argument('-ml-hdf5', '--ml-hdf5', help='Input hdf5 filepath for FCS features \
    [default: db/ML_input.hdf5]',
                        dest='ml_hdf5_fp', default="db/ML_input.hdf5", type=str)
    parser.add_argument('-annot', '--case_annot', help='Tab-separated text table with Case information. \
    Columns must include <case_number>', type=str)
    add_filter_args(parser)


def action(args):
    # Connect to database
    db = FCSdatabase(db=args.db, rebuild=False)

    # Get features_HDF case_tube_idx's
    HDF_feature_obj = HDF5_IO(filepath=args.feature_hdf5_fp,
                              clobber=False)
    #    feature_cti = HDF_feature_obj.get_case_tube_idxs()  #  list of ints()
    feature_cti = [8];     print "TESTING!"

    # Get feature cases list
    feature_cases = db.query(getCases=True,
                             case_tube_idx=feature_cti,
                             aslist=True).results
    # ? unique ?

    # Load annotations (row-index is case_number)
    ann = CustomData(args.case_annot).dat
    ann_cases = ann.index.tolist()

    # Identify annotation cases not represented in HDF5
    exclusions = dict()
    exclusions['no_features'] = [c for c in ann_cases
                                 if c not in feature_cases]

    # Cases to consider (insersection of annotations and HDF5 features)
    cases_to_consider = [c for c in ann_cases
                         if c in feature_cases]

    # Get/pick case, case_tube_idx list
    if args.cases is None:
        args.cases = cases_to_consider
    else:
        raise Exception('Not able to handle this -- should I be able to pass cases here?')
    q = db.query(exporttype='dict_dict', getfiles=True,
                 **vars(args))
    print "WARNING: not yet picking case, case_tube_idx in smart way [so only works for 1:1]"

    case_tube_index_list = []
    case_list = []
    for case, case_info in q.results.items():
        for case_tube_idx, x in case_info.items():
            log.info("Case: %s, Case_tube_idx: %s" % (case, case_tube_idx))
            case_tube_index_list.append(case_tube_idx)
            case_list.append(case)

    # Keep track of cases that were excluded at the query step
    exclusions['excluded by DB query'] = [c for c in cases_to_consider
                                          if c not in case_list]

    # Get features [assuming that features are returned in order!]
    features_df = HDF_feature_obj.make_single_tube_analysis(case_tube_index_list)
    features_df.set_index('bin_num', drop=True, inplace=True)
    features_df.columns = case_list
    features_df = features_df.T
    log.debug(features_df.head())

    # Get annotations [ordered by case_tube_idx]
    annotation_df = ann.loc[case_list, :]
    log.debug(annotation_df.head())

    # TODO:
    # Send features_df, annotation_df, and exclusions to ML_input_HDF5 (args.ml_hdf5_fp)
