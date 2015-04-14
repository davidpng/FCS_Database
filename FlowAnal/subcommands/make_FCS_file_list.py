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
    parser.add_argument('file_list',
                        help='Output filelist of found FCS files', type=str)
    parser.add_argument('-exclude', '--ex', help='List of directories to exclude',
                        default=[".."], nargs='+', type=str)
    parser.add_argument('-n', '--n',
                        help='For testing purposes only find N files',
                        default=None, type=int)


def action(args):
    # Collect files/dirs
    Find_Clinical_FCS_Files(args.dir,
                            exclude=args.ex,
                            Filelist_Path=args.file_list,
                            **vars(args))
