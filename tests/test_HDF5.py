"""
Test FCS functions
"""

import logging
import warnings
from os import path
import datetime
import numpy as np
import pandas as pd
import pickle

from __init__ import TestBase, datadir, write_csv
from FlowAnal.HDF5_IO import HDF5_IO
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.__init__ import package_data, __version__
from pandas.util.testing import assert_frame_equal,assert_almost_equal

log = logging.getLogger(__name__)


def data(fname):
    return path.join(datadir, fname)

#set global variables
coords = {'singlet': [(0.01, 0.06), (0.60, 0.75), (0.93, 0.977), (0.988, 0.86),
              (0.456, 0.379), (0.05, 0.0), (0.0, 0.0)],
          'viable': [(0.358, 0.174), (0.609, 0.241), (0.822, 0.132), (0.989, 0.298),
             (1.0, 1.0), (0.5, 1.0), (0.358, 0.174)]}

comp_file = {'1': package_data('Spectral_Overlap_Lib_LSRA.txt'),
             '2': package_data('Spectral_Overlap_Lib_LSRB.txt'),
             '3': package_data('Spectral_Overlap_Lib_LSRB.txt')}
filename = "12-00031_Myeloid 1.fcs"

class Test_HDF5(TestBase):
    """ Test HDF5_IO subpackage """
    def test_push_pull(self):
        """
        tests HDF5_IO.push_fcs_features 
        """
        #intialize filepaths
        FCS_fp = data(filename)
        DB_fp = path.join(self.mkoutdir(), 'test.db')
        HDF_fp = path.join(self.mkoutdir(), 'test_HDF.hdf5')
        #fcs initilaization
        FCS_obj = FCS(filepath=FCS_fp, import_dataframe=True)
        FCS_obj.comp_scale_FCS_data(compensation_file=comp_file,
                              gate_coords=coords, rescale_lim=(-0.5,1),
                              strict=False, auto_comp=False)
        FCS_obj._feature_extraction(extraction_type='FULL',bins=10)
        log.debug(FCS_obj.FCS_features.histogram)
        #db initialization
        DB_obj = FCSdatabase(db=DB_fp, rebuild=True)
        FCS_obj.meta_to_db(db=DB_obj, dir=path.abspath('.'))
        FCS_obj.get_case_tube_index(db=DB_obj,dir='what')
        log.debug(FCS_obj.case_tube_idx)
        #hdf initialization
        HDF_obj = HDF5_IO(filepath=HDF_fp)
        
        #push fcs_features
        HDF_obj.push_fcs_features(case_tube_idx=FCS_obj.case_tube_idx,
                                  FCS=FCS_obj, db=DB_obj)
        #pull fcs_features
        output = HDF_obj.get_fcs_features(FCS_obj.case_tube_idx)
        log.debug(output)
        np.testing.assert_allclose(output.data,FCS_obj.FCS_features.histogram.data)








