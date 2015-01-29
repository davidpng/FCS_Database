#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Template script for selecting a set of .fcs files and operating on them one-by-one

NOTE: There are some files that are not found because of discordance of filename \
and filename internal to .fcs file (meta info)
"""
import logging
from sets import Set

from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.Feature_IO import Feature_IO
from FlowAnal.MergedFeatures_IO import MergedFeatures_IO
from FlowAnal.CustomData import CustomData
from __init__ import add_filter_args

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('-db', '--db',
                        help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-feature-hdf5', '--feature-hdf5',
                        help='Input hdf5 filepath for FCS features \
    [default: db/fcs_features.hdf5]',
                        dest='feature_hdf5_fp', default="db/fcs_features.hdf5", type=str)
    parser.add_argument('-ml-hdf5', '--ml-hdf5',
                        help='Input hdf5 filepath for FCS features \
    [default: db/ML_input.hdf5]',
                        dest='ml_hdf5_fp', default="db/ML_input.hdf5", type=str)
    parser.add_argument('-annot', '--case_annot',
                        help='Tab-separated text table with Case information. \
    Columns must include <case_number>', type=str)
    add_filter_args(parser)


def action(args):

    argd = vars(args)  # Collect options
    if argd['cases'] is not None or argd['case_tube_idxs'] is not None:
        raise ValueError('Should I be able to pass cases or cti\'s here??')

    # Connect to database
    db = FCSdatabase(db=argd['db'], rebuild=False)

    # Get features_HDF case_tube_idx's
    HDF_feature_obj = Feature_IO(filepath=argd['feature_hdf5_fp'],
                                 clobber=False)
    feature_cti = HDF_feature_obj.get_case_tube_idxs()

    # Load annotations (row-index is case_number)
    ann = CustomData(args.case_annot).dat
    ann_cases = Set(ann.index.tolist())
    log.debug("Annotation cases: {}".format(ann_cases))

    # Get/pick case, case_tube_idx list
    feature_cases = Set(db.query(getCases=True,
                                 aslist=True,
                                 case_tube_idxs=feature_cti).results)
    log.debug("Feature cases: {}".format(feature_cases))

    # Identify annotation cases not represented in HDF5
    exclusions_dic = {}
    exclusions_dic['no_features'] = list(ann_cases - feature_cases)

    # Cases to consider (insersection of annotations and HDF5 features)
    cases_to_consider = ann_cases & feature_cases
    argd['cases'] = list(cases_to_consider)
    argd['case_tube_idxs'] = feature_cti
    q = db.query(pick_cti=True,
                 **argd)
    case_tube_index_list = q.results.case_tube_idx.tolist()
    case_list = Set(q.results.case_number.tolist())
    log.debug('Selected case/cti: {}'.
              format([[list(case_list)[i], case_tube_index_list[i]]
                      for i in range(len(case_tube_index_list))]))

    # Keep track of cases that were excluded at the query step
    exclusions_dic['excluded_by_DB_query'] = list(cases_to_consider - case_list)
    log.debug(exclusions_dic)

    # Get features [assuming that features are returned in order!]
    features_df, not_in_data, merge_fail = HDF_feature_obj.make_single_tube_analysis(case_tube_index_list)
    features_df.set_index('bin_num', drop=True, inplace=True)
    features_df.columns = case_list
    features_df = features_df.T
    log.debug(features_df.head())

    # Get annotations [ordered by case_tube_idx]
    annotation_df = ann.loc[list(case_list), :]
    log.debug(annotation_df.head())

    # Send features_df, annotation_df, and exclusions to ML_input_HDF5 (args.ml_hdf5_fp)
    Merged_ML_feat_obj = MergedFeatures_IO(filepath=args.ml_hdf5_fp,
                                           clobber=True)

    Merged_ML_feat_obj.push_features(features_df)
    Merged_ML_feat_obj.push_annotations(annotation_df)
    Merged_ML_feat_obj.push_not_found(exclusions_dic)  # exclusions is a dictionary
















