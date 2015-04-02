#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Script to select set of .fcs files and then plot processed data as 2d grid
for the purposes of QC for cross-channel bleed

"""
import logging
from os import path

from FlowAnal.Analysis_Variables import gate_coords, comp_file
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.FCS import FCS
from __init__ import add_filter_args, add_process_args

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Base directory containing .fcs files',
                        type=str)
    parser.add_argument('-db', '--db', help='Input sqlite db containing flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-vizmode', '--vizmode', default='comp', type=str,
                        choices=['comp', 'M1_gating'],
                        help='Type of 2D plot to make')
    parser.add_argument('-n_pts', '--n_pts', default=2e5, type=int,
                        help='Number of total points to include when considering plot')
    parser.add_argument('-downsample', '--downsample', default=None, type=float,
                        help='Fraction of points to display')
    parser.add_argument('-export', '--export_data', default=False, action='store_true',
                        help='Whether to print out data table to file')
    parser.add_argument('-cluster', '--cluster', default=False, action='store_true',
                        help='Run clustering algorithm')
    parser.add_argument('-cmethod', '--cluster-method', default='flowPeaks',
                        choices=['flowPeaks'], type=str,
                        help='Which clustering method to use')
    add_filter_args(parser)
    add_process_args(parser)


def action(args):
    # Connect to database
    db = FCSdatabase(db=args.db, rebuild=False)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            log.info("Case: %s, Case_tube_idx: %s, File: %s" % (case, case_tube_idx, relpath))
            filepath = path.join(args.dir, relpath)

            fFCS = FCS(filepath=filepath, import_dataframe=True)
            outfile = 'output/' + '_'.join([case, str(case_tube_idx),
                                            args.vizmode,
                                            fFCS.date.strftime("%Y%m%d")]) + '.png'

            fFCS.comp_scale_FCS_data(compensation_file=comp_file,
                                     gate_coords=gate_coords,
                                     strict=False, **vars(args))
            if args.export_data:
                fFCS.data_to_txt()

            if args.cluster:
                fFCS.cluster(**vars(args))

            fFCS.visualize_2D(outfile=outfile,
                              **vars(args))
