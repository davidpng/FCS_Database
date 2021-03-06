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

from FlowAnal.Feature_IO import Feature_IO
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.Analysis_Variables import gate_coords,comp_file,test_fcs_fn

from FlowAnal.__init__ import package_data, __version__

log = logging.getLogger(__name__)


def data(fname):
    return path.join(datadir, fname)

class Test_Feature_IO(TestBase):
    """ Test Feature_IO subpackage """
    def test_push_pull(self):
        """
        tests Feature_IO.push_fcs_features
        """
        # intialize filepaths
        FCS_fp = data(test_fcs_fn)
        DB_fp = path.join(self.mkoutdir(), 'test.db')
        HDF_fp = path.join(self.mkoutdir(), 'test_Feature_HDF.hdf5')

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

        # hdf initialization
        HDF_obj = Feature_IO(filepath=HDF_fp)

        # push fcs_features
        HDF_obj.push_fcs_features(case_tube_idx=FCS_obj.case_tube_idx,
                                  FCS=FCS_obj, db=DB_obj)

        # pull fcs_features
        output = HDF_obj.get_fcs_features(FCS_obj.case_tube_idx) #test single case retrieval
        log.debug(output)
        np.testing.assert_allclose(output.data, FCS_obj.FCS_features.histogram.data)
        
        cti_list = pd.DataFrame(data= np.array([['13-12345','1',"Dummy Error"]]),
                                index=[1],
                                columns=['casenum','cti','errormessage'])
        # push failed_cti list to "meta data"
        HDF_obj.push_failed_cti_list(cti_list)
                
        # pull meta data from HDF5 file
        meta_data = HDF_obj.get_meta_data()
        log.debug("File meta data is {}".format(meta_data))
        
        








