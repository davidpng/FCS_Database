# -*- coding: utf-8 -*-
"""
Created on Mon Oct 20 13:56:55 2014

@author: ngdavid
"""
import os.path
import fnmatch
Dir = "/home/ngdavid/Desktop/Ubuntu_Dropbox/Myeloid_Data/Myeloid"

filenames = [os.path.join(dir, f)
    for dirpath, dirnames, files in os.walk(path)
    for f in fnmatch.filter(files, '*.txt')]