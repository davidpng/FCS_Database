#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Identifies FCS files in specified directory and outputs list to file

"""
import logging
from FlowAnal.Find_Clinical_FCS_Files import Find_Clinical_FCS_Files

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Directory with Flow FCS files [required]',
                        type=str)
    parser.add_argument('-fl', '--fl', help='Output filelist of found FCS files\
    [default: db/FoundFile.txt]', default='db/FoundFile.txt', type=str)
    parser.add_argument('-exclude', '--ex', help='List of directories to exclude',
                        default=[".."], nargs='+', type=str)
    parser.add_argument('-testing', '--testing', help='For testing purposes only find ~10 files',
                        action='store_true')


def action(args):
    # Collect files/dirs
    Find_Clinical_FCS_Files(args.dir,
                            exclude=args.ex,
                            Filelist_Path=args.fl,
                            **vars(args))
