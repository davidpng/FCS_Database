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
    #parser.add_argument('-db', '--db', help='Input sqlite3 db for Flow meta data \
    #[default: db/fcs.db]',
    #                    default="db/fcs.db", type=str)
    #parser.add_argument('-ft', '--feature_hdf5', help="HDF5 filepath for FCS \
    #                    features [default: db/fcs_features.hdf5]",
    #                    dest='feature_fp', default="db/fcs_features.hdf5", type=str)
    parser.add_argument('-mf', '--ML_input_hdf5', help="Output hdf5 filepath for \
                        Merged Data [default: db/ML_input.hdf5]",
                        dest='MLinput_fp', default="ML_input.hdf5", type=str)

    #parser.add_argument('-method', '--feature-extration-method',
    #                    help='The method to use to extract features [default: Full]',
    #                    default='Full', type=str, dest='feature_extraction_method')
    #add_filter_args(parser)


def action(args):

    # Import  MergedData
    MLinput_obj = MergedFeatures_IO(filepath=args.MLinput_fp, clobber=False)
    Feature_DF = MLinput_obj.get_features()
    Annotation_DF = MLinput_obj.get_annotations()
    not_found = MLinput_obj.get_not_found()
    print Feature_DF
    print Annotation_DF
	
