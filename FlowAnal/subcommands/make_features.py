#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Builds HDF5 file with features from FCS data

"""
import logging
from os import path
import sys
from sqlalchemy.exc import IntegrityError

from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.__init__ import package_data
from FlowAnal.HDF5_IO import HDF5_IO
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
    parser.add_argument('-hdf5', '--feature-hdf5', help='Output hdf5 filepath for FCS features \
    [default: db/fcs_features.hdf5]', dest='hdf5_fp',
                        default="db/fcs_features.hdf5", type=str)
    parser.add_argument('-method', '--feature-extration-method',
                        help='The method to use to extract features [default: Full]',
                        default='Full', type=str, dest='feature_extraction_method')
    add_filter_args(parser)


def action(args):
    log.info('Creating hdf5 file [%s] with features extracted by method [%s]' %
             (args.hdf5_fp, args.feature_extraction_method))

    # Connect to database
    log.info("Loading database input %s" % args.db)
    db = FCSdatabase(db=args.db, rebuild=False)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    # Create HDF5 object
    HDF_obj = HDF5_IO(filepath=args.hdf5_fp, clobber=True)

    # initalize empty list to append case_tube_idx that failed feature extraction
    feature_failed_CTIx = []
    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            log.info("Case: %s, Case_tube_idx: %s, File: %s" % (case, case_tube_idx, relpath))
            filepath = path.join(args.dir, relpath)
            fFCS = FCS(filepath=filepath, import_dataframe=True)

            try:
                fFCS.comp_scale_FCS_data(compensation_file=comp_file,
                                         gate_coords=coords,
                                         rescale_lim=(-0.5, 1),
                                         strict=False, auto_comp=False)
                fFCS.feature_extraction(extraction_type=args.feature_extraction_method,
                                        bins=10)
                HDF_obj.push_fcs_features(case_tube_idx=case_tube_idx,
                                          FCS=fFCS, db=db)
            except ValueError, e:
                print("Skipping feature extraction for case: {} \
                because of 'ValueError {}'".format(case, e))
                feature_failed_CTIx.append([case, case_tube_idx, e])
            except KeyError, e:
                print "Skipping FCS %s because of KeyError: %s" % (filepath, e)
                feature_failed_CTIx.append([case, case_tube_idx, e])
            except IntegrityError, e:
                print "Skipping Case: {}, Tube: {}, Date: {}, filepath: {} because \
                of IntegrityError: {}".format(case, case_tube_idx, filepath, e)
                feature_failed_CTIx.append([case, case_tube_idx, e])
            except:
                print "Skipping FCS %s because of unknown error related to: %s" % \
                    (filepath, sys.exc_info()[0])
                feature_failed_CTIx.append([case, case_tube_idx, sys.exc_info()[0]])

    log.info("Case_tubes that failed feature extraction: {}".format(feature_failed_CTIx))

    # push feature_failed_CTIx to database and removed Cases that did not extract for a
    # NB: feature_failed CTIx is a list of lists with (case, case_tube_idx, error message)
