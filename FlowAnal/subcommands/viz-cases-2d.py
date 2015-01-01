#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Script to select set of .fcs files and then plot processed data as 2d grid
for the purposes of QC for cross-channel bleed


"""
import logging
from os import path

from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.FCS import FCS
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
    parser.add_argument('dir', help='Base directory containing .fcs files',
                        type=str)
    parser.add_argument('-tubes', '--tubes', help='List of tube types to select',
                        nargs='+', action='store',
                        default=None, type=str)
    parser.add_argument('-cases', '--cases', help='List of cases to select',
                        nargs='+', action='store',
                        default=None, type=str)
    parser.add_argument('-dates', '--daterange',
                        help='Start and end dates to bound selection of cases \
                        [Year-Month-Date Year-Month-Date]',
                        nargs=2, action='store', type=str)
    parser.add_argument('-db', '--db', help='Input sqlite db containing flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-n', '--n_files', help='For testing purposes only find N files',
                        default=None, type=int)


def action(args):
    # Connect to database
    db = FCSdatabase(db=args.db, rebuild=False)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    i = 0
    done = False
    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            log.info("Case: %s, Case_tube_idx: %s, File: %s" % (case, case_tube_idx, relpath))
            filepath = path.join(args.dir, relpath)

            a = FCS(filepath=filepath, import_dataframe=True)
            a.comp_scale_FCS_data(compensation_file=comp_file,
                                  gate_coords=coords,
                                  strict=False, auto_comp=False)
            outfile = 'output/' + '_'.join([case, str(case_tube_idx),
                                            a.case_tube.replace(' ', '_'),
                                            a.date.strftime("%Y%m%d")]) + '.png'
            a.comp_visualize_FCS(outfile=outfile)

            i += 1
            if args.n_files is not None and i >= args.n_files:
                done = True
                break
        if done is True:
            break

