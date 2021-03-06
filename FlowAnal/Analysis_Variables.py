#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on: Fri 09 Jan 2015 11:19:55 AM PST 
This file sets up analysis variables for testing and analysis
imported from

from FlowAnal.Analysis_Variables import gate_coords,comp_file,test_fcs_fn

@author: ngdavid
"""
__author__ = "David Ng, MD"
__copyright__ = "Copyright 2014, David Ng"
__license__ = "GPL v3"
__version__ = "1.0"
__maintainer__ = "David Ng"
__email__ = "ngdavid@uw.edu"
__status__ = "Production"

from FlowAnal.__init__ import package_data

# set global variables
gate_coords = {'singlet': [(0.01, 0.06), (0.60, 0.75), (0.93, 0.977), (0.988, 0.86),
                           (0.456, 0.379), (0.05, 0.0), (0.0, 0.0)],
               'viable':  [(0.358, 0.174), (0.609, 0.241), (0.822, 0.132), (0.989, 0.298),
                           (1.0, 1.0), (0.5, 1.0), (0.358, 0.174)]}

comp_file = {'1': package_data('Spectral_Overlap_Lib_LSRA.txt'),
             '2': package_data('Spectral_Overlap_Lib_LSRB.txt'),
             '3': package_data('Spectral_Overlap_Lib_LSRB.txt')}

test_fcs_fn = "12-00031_Myeloid 1.fcs"
