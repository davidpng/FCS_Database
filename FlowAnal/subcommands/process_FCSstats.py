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


def action(args):
        # Connect to database
        db = FCSdatabase(db=args.db, rebuild=False)
        print "Processing database %s" % args.db

        # Get QC data
        qc = FlowQC(db=db, table_format='wide')

        log.info(qc.histos)
        log.info(qc.stats)
