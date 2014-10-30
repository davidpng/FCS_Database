# -*- coding: utf-8 -*-
"""
Created on Mon Oct 20 13:56:55 2014
Main Function 
@author: ngdavid
"""
from Find_Clinical_FCS_Files import Find_Clinical_FCS_Files
from FCS import FCS

import argparse

parser = argparse.ArgumentParser(description='Finds FCS files in a directory \
                                              and scrapes metadata')
parser.add_argument('-d', dest = "directory", type = str, required = False,
                   help='root directory location')

inputs = parser.parse_args()
Dir = inputs.directory

Dir = "/home/ngdavid/Desktop/MDS_Plates/Hodgkin_Cases_2008_2013"

Finder = Find_Clinical_FCS_Files(Dir)

FCS_metadata = []
for f in Finder.filenames:
    try:
        FCS_obj = FCS(version=1,filepath=f)
        FCS_obj.comp_scale_FCS_data(comp_file)
        
    except ValueError:
        print "Error Occured"
 

caselist = [i.case_number[0] for i in FCS_metadata]
sizelist = [i.num_events for i in FCS_metadata]
dates = [i.date for i in FCS_metadata]
"""
import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter

years = YearLocator()   # every year
months = MonthLocator()  # every month
yearsFmt = DateFormatter('%Y')

d = dates
v = sizelist
MonthLocator()

fig, ax = plt.subplots()
ax.plot_date(d, v, 'x')

# format the ticks
ax.xaxis.set_major_locator(years)
ax.xaxis.set_major_formatter(yearsFmt)
ax.xaxis.set_minor_locator(months)
"""