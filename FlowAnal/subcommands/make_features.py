#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sat 27 DEC 2014 02:07:37 PM PST
Builds HDF5 file with features from FCS data

"""

__author__ = "David Ng, MD"
__copyright__ = "Copyright 2014"
__license__ = "GPL v3"
__version__ = "1.0"
__maintainer__ = "Daniel Herman"
__email__ = "ngdavid@uw.edu"
__status__ = "Production"

import logging
import pandas as pd
from itertools import chain

from os import path
import sys
import traceback

from __init__ import add_filter_args, add_process_args

from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.Feature_IO import Feature_IO
from FlowAnal.Analysis_Variables import gate_coords, comp_file

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Directory with Flow FCS files [required]',
                        type=str)
    parser.add_argument('-db', '--db', help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-feature-hdf5', '--feature-hdf5', help='Output hdf5 filepath for FCS features \
    [default: db/fcs_features.hdf5]', dest='hdf5_fp',
                        default="db/fcs_features.hdf5", type=str)
    parser.add_argument('-method', '--feature-extration-method',
                        help='The method to use to extract features [default: Full]',
                        default='2d', type=str, dest='feature_extraction_method',
                        choices=['full', '2d'])
    parser.add_argument('-bins', '--bins', default=10, type=int, help='Number of bins to extract')
    parser.add_argument('-exclude', '--params-to-exclude', dest='params_to_exclude',
                        help='List of parameters to exclude from extraction',
                        nargs='+', type=str, default=['Time'])
    parser.add_argument('-rebuild', '--rebuild', help='Wipe and rebuild Feature-hdf5 file',
                        type=bool,
                        default=True, dest='clobber')
    parser.add_argument('-feature_label', '--label_features_with',
                        help='What field to use to label features',
                        default='Antigen', type=str)
    add_filter_args(parser)
    add_process_args(parser)


def action(args):
    log.info('Creating hdf5 file [%s] with features extracted by method [%s]' %
             (args.hdf5_fp, args.feature_extraction_method))

    # Connect to database
    log.info("Loading database input %s" % args.db)
    db = FCSdatabase(db=args.db, rebuild=False)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    # Create HDF5 object
    HDF_obj = Feature_IO(filepath=args.hdf5_fp, clobber=args.clobber)

    # initalize empty list to append case_tube_idx that failed feature extraction
    feature_failed_CTIx = []

    num_results = len(list(chain(*q.results.values())))
    i = 1
    log.info("Found {} case_tube_idx's".format(num_results))
    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            # this nested for loop iterates over all case_tube_idx
            log.info("Case: %s, Case_tube_idx: %s, File: %s [%s of %s]" %
                     (case, case_tube_idx, relpath, i, num_results))
            filepath = path.join(args.dir, relpath)
            fFCS = FCS(filepath=filepath, case_tube_idx=case_tube_idx, import_dataframe=True)

            try:
                fFCS.comp_scale_FCS_data(compensation_file=comp_file,
                                         gate_coords=gate_coords,
                                         strict=False, **vars(args))
                fFCS.feature_extraction(extraction_type=args.feature_extraction_method,
                                        bins=args.bins,
                                        exclude_params=args.params_to_exclude,
                                        label_with=args.label_features_with)
                HDF_obj.push_fcs_features(case_tube_idx=case_tube_idx,
                                          FCS=fFCS, db=db)
            except Exception as ex:
                print "Skipping FCS [{}] because of unknown error related to {}: {}".\
                    format(filepath, ex.__class__, ex.message)
                traceback.print_exc(file=sys.stdout)
                feature_failed_CTIx.append([case, case_tube_idx, ex.message])
            print("{:6d} of {} cases found and loaded\r".format(i, num_results)),

            i += 1

    if feature_failed_CTIx == []:
        # if no features failed, we will create a dummy dataframe to load
        # otherwise when reading this will cause a failure
        failed_DF = pd.DataFrame([['NaN', 'NaN', 'NaN']],
                                 columns=['case_number', 'case_tube_idx', 'error_message'])
        log.info("Nothing failed feature extraction!")
    else:
        failed_DF = pd.DataFrame(feature_failed_CTIx,
                                 columns=['case_number', 'case_tube_idx', 'error_message'])
        log.info("Case_numbers that failed feature extraction: {}".
                 format(failed_DF.case_number.unique()))
        log.info("Case_tubes that failed feature extraction: {}".
                 format(failed_DF.case_tube_idx.unique()))

    HDF_obj.push_failed_cti_list(failed_DF)


