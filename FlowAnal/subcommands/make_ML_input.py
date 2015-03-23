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
    parser.add_argument('-sep', '--sep',
                        help='Annotation field separator',
                        default='\t', type=str)
    add_filter_args(parser)


def action(args):

    argd = vars(args)  # Collect options
    if argd['cases'] is not None or argd['case_tube_idxs'] is not None:
        raise ValueError('Should I be able to pass cases or cti\'s here??')

    # Connect to database
    db = FCSdatabase(db=argd['db'], rebuild=False)

    # Get list of ctis in features_HDF
    HDF_feature_obj = Feature_IO(filepath=argd['feature_hdf5_fp'],
                                 clobber=False)
    feature_cti = HDF_feature_obj.get_case_tube_idxs()

    # Load annotations (row-index is case_number)
    ann = CustomData(args.case_annot, args.sep).dat
    ann_cases = Set(ann.index.tolist())
    log.info("Found {} cases with annotations".format(len(ann_cases)))
    log.debug("Annotation cases: {}".format(ann_cases))

    # Get cti, case from db for ctis in features_HDF
    feature_cases_ctis = db.query(getCases=True,
                                  aslist=True,
                                  case_tube_idxs_list=feature_cti).results
    feature_cti, feature_cases = zip(*feature_cases_ctis)
    feature_cases = Set(feature_cases)
    log.info('Found features for {} ctis and {} cases'.format(len(feature_cti),
                                                              len(feature_cases)))
    log.debug("Feature cases: {}".format(feature_cases))

    # Identify annotation cases not represented in HDF5
    exclusions_dic = {}
    exclusions_dic['no_features'] = list(ann_cases - feature_cases)

    # Cases to consider (insersection of annotations and HDF5 features)
    cases_to_consider = ann_cases & feature_cases
    log.info('Considering {} cases'.format(len(cases_to_consider)))
    log.info('Excluded {} cases because there were no features'.format(len(exclusions_dic['no_features'])))
    cc_to_consider = {}
    for x in [y for y in feature_cases_ctis
              if y[1] in ann_cases]:
        if x[1] in cc_to_consider:
            cc_to_consider[x[1]].append(x[0])
        else:
            cc_to_consider[x[1]] = [x[0]]

    # Pick most recent cti for each case
    q = db.query(pick_cti=True,
                 cc_list=cc_to_consider,
                 **argd).results
    case_tube_index_list = zip(*q)[0]
    case_list = Set(zip(*q)[1])

    # Keep track of cases that were excluded at the query step
    exclusions_dic['excluded_by_DB_query'] = list(cases_to_consider - case_list)
    log.info('Excluded {} cases in query step'.format(len(exclusions_dic['excluded_by_DB_query'])))
    log.debug(exclusions_dic)

    # Get features [assuming that features are returned in order!]
    features_df, not_in_data, merge_fail = HDF_feature_obj.make_single_tube_analysis(case_tube_index_list)
    features_df.columns = case_list
    features_df = features_df.T
    log.debug(features_df.head())

    # Get annotations [ordered by case_tube_idx]
    annotation_df = ann.loc[list(case_list), :]
    log.debug(annotation_df.head())

    # Send features_df, annotation_df, and exclusions to ML_input_HDF5 (args.ml_hdf5_fp)
    Merged_ML_feat_obj = MergedFeatures_IO(filepath=args.ml_hdf5_fp,
                                           clobber=True)
    Merged_ML_feat_obj.push_all(feat_DF=features_df,
                                anno_DF=annotation_df,
                                fail_DF=exclusions_dic,
                                feat_HDF=HDF_feature_obj)
