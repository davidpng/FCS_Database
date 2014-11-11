#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Builds sqlite database with the meta information of all flow files under specified directory

"""
import logging

from FlowAnal.Find_Clinical_FCS_Files import Find_Clinical_FCS_Files
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
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
    parser.add_argument('dir', help='Directory with Flow FCS files [required]',
                        type=str)
    parser.add_argument('-db', '--db', help='Output sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)


def action(args):
        # Collect files/dirs
        Finder = Find_Clinical_FCS_Files(args.dir)

        # Connect to database (and rebuild)
        db = FCSdatabase(db=args.db, rebuild=False)
        print "Building database %s" % args.db

        # Process files/dirs
        for f in Finder.filenames:
            fFCS = FCS(filepath=f, import_dataframe=True)
            if fFCS.empty is False:
                try:
                    fFCS.comp_scale_FCS_data(compensation_file=comp_file,
                                             gate_coords=coords,
                                             strict=False, auto_comp=False)
                    fFCS.extract_FCS_histostats()
                    fFCS.histostats_to_db(db=db)
                except ValueError, e:
                    log.debug("Skipping FCS %s because of %s" % (f, e))

