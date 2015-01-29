"""
Test Merged Feature IO functions
"""

import logging
import warnings
from os import path
import datetime
import numpy as np
import pandas as pd
import pickle

from __init__ import TestBase, datadir, write_csv
from FlowAnal.Feature_IO import Feature_IO
from FlowAnal.MergedFeatures_IO import MergedFeatures_IO
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.Analysis_Variables import gate_coords,comp_file,test_fcs_fn
from FlowAnal.__init__ import package_data, __version__

log = logging.getLogger(__name__)


def data(fname):
    return path.join(datadir, fname)

class Test_ML_input_IO(TestBase):
    """ Test MergedFeatures_IO subpackage """
    def test_ML_push_pull(self):
        """
        tests MergedFeature_IO.push_fcs_features
        """
        # intialize filepaths
        FCS_fp = data(test_fcs_fn)
        DB_fp = path.join(self.mkoutdir(), 'test.db')
        FT_HDF_fp = path.join(self.mkoutdir(), 'test_FT_HDF.hdf5')
        ML_HDF_fp = path.join(self.mkoutdir(), 'test_ML_HDF.hdf5')

        # fcs initilaization
        FCS_obj = FCS(filepath=FCS_fp, import_dataframe=True)
        FCS_obj.comp_scale_FCS_data(compensation_file=comp_file,
                                    gate_coords=gate_coords, rescale_lim=(-0.5, 1),
                                    strict=False, auto_comp=False)
        FCS_obj.feature_extraction(extraction_type='Full', bins=10)
        log.debug(FCS_obj.FCS_features.histogram)

        # db initialization
        DB_obj = FCSdatabase(db=DB_fp, rebuild=True)
        FCS_obj.meta_to_db(db=DB_obj, dir=path.abspath('.'))
        log.debug(FCS_obj.case_tube_idx)

        # feature hdf initialization
        FT_HDF_obj = Feature_IO(filepath=FT_HDF_fp)

        # push fcs_features
        FT_HDF_obj.push_fcs_features(case_tube_idx=FCS_obj.case_tube_idx,
                                     FCS=FCS_obj, db=DB_obj)
        
        feature_DF,not_in_data,merge_fail = FT_HDF_obj.make_single_tube_analysis([FCS_obj.case_tube_idx])

        ML_HDF_obj = MergedFeatures_IO(filepath=ML_HDF_fp,clobber=True)
        
        ML_HDF_obj.push_features(feature_DF)
        
        ML_HDF_obj.push_annotations(pd.DataFrame([[test_fcs_fn,0]],
                                    columns=['case_num','annotation']))



