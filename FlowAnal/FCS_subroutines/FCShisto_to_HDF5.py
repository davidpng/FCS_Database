# -*- coding: utf-8 -*-
"""
Created on Wed 31 Dec 2014 05:54:41 AM PST 
This file describes a HDF5 interface class for pushing 'binned' histograms
to an HDF5 file format
@author: David Ng, MD
"""
import h5py

class FCShisto_to_HDF5(object):
    def __init__(self,filename,histo_object,verbose,overwrite=False):
        """
        need case_tube_idx
        """
        fh = h5py.File(filename,'w')
        
        schema = ["/database_info_version",
                  "/query",
                  "/case_list,"
                  "/data/"+case_tube_idx+"/data",
                  "/data/"+case_tube_idx+"/indices",
                  "/data/"+case_tube_idx+"/indptr",
                  "/data/"+case_tube_idx+"/shape"]

