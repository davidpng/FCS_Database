#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Collects and process flow QC data

"""
import logging

from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.FlowQC import FlowQC

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('--db', '-db', help='sqlite3 db with flow meta data \
    [default: db/fcs_stats.db]',
                        default="db/fcs_stats.db", type=str)
    parser.add_argument('-tubes', '--tubes', help='List of tube types to select',
                        nargs='+', action='store',
                        default=None, type=str)
    parser.add_argument('-dates', '--daterange',
                        help='Start and end dates to bound selection of cases \
                        [Year-Month-Date Year-Month-Date]',
                        nargs=2, action='store', type=str)
    parser.add_argument('-testing', '--testing',
                        action='store_true')
    parser.add_argument('-table-format', '--table-format', dest='table_format',
                        default='tall', type=str)
    parser.add_argument('-cases', '--cases', help='List of cases to select',
                        nargs='+', action='store',
                        default=None, type=str)


def action(args):
        # Connect to database
        dbcon = FCSdatabase(db=args.db, rebuild=False)
        print "Processing database %s" % args.db

        # Get QC data
        if args.testing:
            testdbcon = FCSdatabase(db='db/test.db', rebuild=True)
            args.table_format = 'tall'
            qc = FlowQC(dbcon=dbcon, **vars(args))
            qc.pushQC(db=testdbcon)
        else:
            qc = FlowQC(dbcon=dbcon, **vars(args))

        log.debug(qc.histos)
        log.debug(qc.PmtStats)
        log.debug(qc.TubeStats)

