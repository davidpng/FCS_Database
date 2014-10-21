# -*- coding: utf-8 -*-
"""
Created on Mon Oct 20 13:56:55 2014

@author: ngdavid
"""
from HEADER_Find_FCS_Files import Find_Clinical_FCS_Files
from HEADER_loadFCS import loadFCS

import argparse

parser = argparse.ArgumentParser(description='Finds FCS files in a directory \
                                              and scrapes metadata')
parser.add_argument('-d', dest = "directory", type = str, required = True,
                   help='root directory location')

inputs = parser.parse_args()
Dir = inputs.directory

#Dir = "/home/ngdavid/Desktop/Ubuntu_Dropbox/Myeloid_Data/Myeloid"

Finder = Find_Clinical_FCS_Files(Dir)

FCS_metadata = []
for f in Finder.filenames:
    FCS_metadata.append( loadFCS(f) )
    print FCS_metadata