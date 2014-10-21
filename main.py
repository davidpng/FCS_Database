# -*- coding: utf-8 -*-
"""
Created on Mon Oct 20 13:56:55 2014

@author: ngdavid
"""
from HEADER_Find_FCS_Files import Find_Clinical_FCS_Files
from HEADER_loadFCS import loadFCS

Dir = "/home/ngdavid/Desktop/Ubuntu_Dropbox/Myeloid_Data/Myeloid"

Finder = Find_Clinical_FCS_Files(Dir)

FCS_metadata = []
for f in Finder.filenames:
    FCS_metadata.append( loadFCS(f) )
    