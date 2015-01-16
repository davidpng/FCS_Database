#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Template for selecting a set of
NOTE: There are some files that are not found because of discordance of filename \
and filename internal to .fcs file (meta info)
"""
import logging

from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.Feature_IO import Feature_IO
from FlowAnal.MergedFeatures_IO import MergedFeatures_IO
from __init__ import add_filter_args

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('-db', '--db', help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-ft', '--feature_hdf5', help="HDF5 filepath for FCS \
                        features [default: db/fcs_features.hdf5]",
                        dest='feature_fp', default="db/fcs_features.hdf5", type=str)
    parser.add_argument('-mf', '--ML_input_hdf5', help="Output hdf5 filepath for \
                        Merged Data [default: db/ML_input.hdf5]",
                        dest='MLinput_fp', default="db/ML_input.hdf5", type=str)

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
    Feature_obj = Feature_IO(filepath=args.feature_fp, clobber=False)
    features_df, not_in_cti, merge_fail_cti = Feature_obj.make_single_tube_analysis(case_tube_list)
    log.debug("Feature DF: {} \n Case_tube_indices that failed: {}".format(
                                           features_df.head(), merge_fail_cti))

    # Get annotations [ordered by case_tube_idx]
    annotation_df = db.query(exporttype='df', getCaseAnnotations=True, **vars(args)).results
    log.debug(annotation_df.head())

    # this is a dummy for now, not sure where to generate this list from.
    """Function to convert merge_fail_cti to merge_fail_case_nums"""
    """Not sure what error codes to provide"""
    not_found_df = pd.DataFrame(['12-12345', 'Not found'], columns=["case_num", "error_code"])

    """This has only been partially tested, can not be done without an annotation_df"""
    # Open/Create MergedData
    MLinput_obj = MergedFeatures_IO(filepath=args.MLinput_fp, clobber=True)
    MLinput_obj.push_features(features_df)
    MLinput_obj.push_annotations(annotation_df)
    MLinput_obj.push_not_found(not_found_df)


