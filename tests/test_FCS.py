"""
Test FCS functions
"""

import logging
import warnings
from os import path
import datetime
import numpy as np
import pandas as pd

from __init__ import TestBase, datadir
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.__init__ import package_data, __version__

log = logging.getLogger(__name__)


def data(fname):
    return path.join(datadir, fname)


class Test_FCS(TestBase):
    """ Test FCS subpackage """

    def test_loadFCS(self):
        """ Testing loading FCS from file using FCS and loadFCS modules """

        filename = "12-00031_Myeloid 1.fcs"
        filepath = data(filename)
        a = FCS(filepath=filepath, import_dataframe=True)

        self.assertFalse(a.empty)
        self.assertEqual(a.filepath, filepath)
        self.assertEqual(a.filename, filename)
        self.assertEqual(a.case_number, '12-00031')
        self.assertEqual(a.cytometer, 'LSRII - A (LSRII)')
        self.assertEqual(a.date, datetime.datetime(2012, 1, 3, 12, 0, 15))
        self.assertEqual(a.case_tube, '12-00031_Myeloid 1')
        self.assertEqual(a.num_events, 160480)
        self.assertEqual(a.version, __version__)
        self.assertTrue(hasattr(a, 'data'))

        parameters = {'Optical Filter Name': np.nan, 'Excitation Wavelength': np.nan,
                      'Amp type': '0,0', 'Excitation Power': np.nan, 'Antigen': 'CD15',
                      'Detector Type': np.nan, 'Short name': 'FITC-H', 'suggested scale': np.nan,
                      'Channel Name': 'CD15 FITC',
                      'Voltage': 465, 'Amp gain': '1.0',
                      'Range': 262144, 'Channel Number': 5, 'Bits': 32, 'Fluorophore': 'FITC'}
        self.assertEqual(dict(a.parameters.loc[:, 'FITC-H']), parameters)

    def test_empty_FCS(self):
        """ Testing loading FCS filepath that does not load properly ==> empty """

        filename = "99-80923_Fake.fcs"
        filepath = data(filename)

        with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                a = FCS(filepath=filepath)

        self.assertEqual(a.filepath, filepath)
        self.assertEqual(a.filename, filename)
        self.assertEqual(a.case_number, '99-80923')
        self.assertFalse(hasattr(a, 'num_events'))

    def test_meta_to_db(self):
        """ Make sure that the push of meta data to db 'runs'

        NOTE: not explicitly checking what is in the db
        """

        root_dir = path.abspath('.')
        outfile = path.join(self.mkoutdir(), 'test.db')
        filename = "12-00031_Myeloid 1.fcs"
        filepath = path.abspath(data(filename))

        a = FCS(filepath=filepath)

        # from FlowAnal.database.FCS_database import FCSdatabase
        db = FCSdatabase(db=outfile, rebuild=True)

        a.meta_to_db(db=db, dir=root_dir)
        
    def test_comp_vis(self):
        """ 
        Tests the compensation visualizer subroutine in FCS
        """

        coords = {'singlet': [(0.01, 0.06), (0.60, 0.75), (0.93, 0.977), (0.988, 0.86),
                              (0.456, 0.379), (0.05, 0.0), (0.0, 0.0)],
                  'viable': [(0.358, 0.174), (0.609, 0.241), (0.822, 0.132), (0.989, 0.298),
                             (1.0, 1.0), (0.5, 1.0), (0.358, 0.174)]}

        comp_file = {'1': package_data('Spectral_Overlap_Lib_LSRA.txt'),
                     '2': package_data('Spectral_Overlap_Lib_LSRB.txt'),
                     '3': package_data('Spectral_Overlap_Lib_LSRB.txt')}
        filename = "12-00031_Myeloid 1.fcs"
        filepath = data(filename)
        a = FCS(filepath=filepath, import_dataframe=True)
        a.comp_scale_FCS_data(compensation_file=comp_file,
                              gate_coords=coords,
                              strict=False,auto_comp=False)
                             
        a.comp_visualize_FCS(filename='dummy.pdf')
        
    def test_process(self):
        """ Test running processing

        Looking at small set of events (100:105) and FSC and CD15 channel and making sure \
        that result is the same as when this function was initially setup
        """

        coords = {'singlet': [(0.01, 0.06), (0.60, 0.75), (0.93, 0.977), (0.988, 0.86),
                              (0.456, 0.379), (0.05, 0.0), (0.0, 0.0)],
                  'viable': [(0.358, 0.174), (0.609, 0.241), (0.822, 0.132), (0.989, 0.298),
                             (1.0, 1.0), (0.5, 1.0), (0.358, 0.174)]}

        comp_file = {'1': package_data('Spectral_Overlap_Lib_LSRA.txt'),
                     '2': package_data('Spectral_Overlap_Lib_LSRB.txt'),
                     '3': package_data('Spectral_Overlap_Lib_LSRB.txt')}
        filename = "12-00031_Myeloid 1.fcs"
        filepath = data(filename)
        a = FCS(filepath=filepath, import_dataframe=True)
        a.comp_scale_FCS_data(compensation_file=comp_file,
                              gate_coords=coords,
                              strict=False,)

        cols = ['FSC-H', 'CD15 FITC']
        b = a.data.loc[100:105, cols]

        b_expect = pd.DataFrame({'FSC-H': {105: 0.25751877, 100: 0.29451752,
                                           101: 0.32627106, 102: 0.42173004},
                                 'CD15 FITC': {105: 0.20802763, 100: 0.20469858,
                                               101: 0.5515328, 102: 0.10146696}}, dtype='float32')
        #np.testing.assert_array_equal(b.loc[:, cols].values, b_expect.loc[:, cols].values)
        np.testing.assert_allclose(b.loc[:, cols].values, b_expect.loc[:, cols].values,
                                   rtol=1e-3,atol=0,err_msg="Results are more different \
                                   than tolerable")
    def test_HistoStats(self):
        """ Tests the HistoStats information subroutines
        :return:
        """
        coords = {'singlet': [(0.01, 0.06), (0.60, 0.75), (0.93, 0.977), (0.988, 0.86),
                              (0.456, 0.379), (0.05, 0.0), (0.0, 0.0)],
                  'viable': [(0.358, 0.174), (0.609, 0.241), (0.822, 0.132), (0.989, 0.298),
                             (1.0, 1.0), (0.5, 1.0), (0.358, 0.174)]}

        comp_file = {'1': package_data('Spectral_Overlap_Lib_LSRA.txt'),
                     '2': package_data('Spectral_Overlap_Lib_LSRB.txt'),
                     '3': package_data('Spectral_Overlap_Lib_LSRB.txt')}

        filename = "12-00031_Myeloid 1.fcs"
        filepath = data(filename)
        a = FCS(filepath=filepath, import_dataframe=True)
        a.comp_scale_FCS_data(compensation_file=comp_file,
                              gate_coords=coords,
                              strict=False, auto_comp=False)
        a.extract_FCS_histostats()

        log.debug(a.stats)
        log.debug(a.histos)
        
    def test_comp_vis(self):
        """
        Tests the comp vizulization subroutine in FCS
        """        
        coords = {'singlet': [(0.01, 0.06), (0.60, 0.75), (0.93, 0.977), (0.988, 0.86),
                              (0.456, 0.379), (0.05, 0.0), (0.0, 0.0)],
                  'viable': [(0.358, 0.174), (0.609, 0.241), (0.822, 0.132), (0.989, 0.298),
                             (1.0, 1.0), (0.5, 1.0), (0.358, 0.174)]}

        comp_file = {'1': package_data('Spectral_Overlap_Lib_LSRA.txt'),
                     '2': package_data('Spectral_Overlap_Lib_LSRB.txt'),
                     '3': package_data('Spectral_Overlap_Lib_LSRB.txt')}

        Convert_CytName = {'H0152':'1', 'H4710082':'3',
                           '1':'1', '2':'2', '3':'3'}

        filename = "12-00031_Myeloid 1.fcs"
        filepath = data(filename)
        a = FCS(filepath=filepath, import_dataframe=True)
        a.comp_scale_FCS_data(compensation_file=comp_file,
                              gate_coords=coords,
                              strict=False,auto_comp=False)

        a.comp_visualize_FCS(filename = 'test.png')
        
    def test_auto_comp(self):
        """ Tests the auto compensation subroutine of comp_scale_FCS_data

        This function will provide testing of the auto_comp_tweak function called \
        by comp_scale_FCS_data when auto_comp flag is turned on.
        """

        coords = {'singlet': [(0.01, 0.06), (0.60, 0.75), (0.93, 0.977), (0.988, 0.86),
                              (0.456, 0.379), (0.05, 0.0), (0.0, 0.0)],
                  'viable': [(0.358, 0.174), (0.609, 0.241), (0.822, 0.132), (0.989, 0.298),
                             (1.0, 1.0), (0.5, 1.0), (0.358, 0.174)]}

        comp_file = {'1': package_data('Spectral_Overlap_Lib_LSRA.txt'),
                     '2': package_data('Spectral_Overlap_Lib_LSRB.txt'),
                     '3': package_data('Spectral_Overlap_Lib_LSRB.txt')}

        Convert_CytName = {'H0152':'1', 'H4710082':'3',
                           '1':'1', '2':'2', '3':'3'}

        filename = "12-00031_Myeloid 1.fcs"
        filepath = data(filename)
        a = FCS(filepath=filepath, import_dataframe=True)
        a.comp_scale_FCS_data(compensation_file=comp_file,
                              gate_coords=coords,
                              strict=False,auto_comp=False)

        cols = ['FSC-H', 'CD15 FITC']
        b = a.data.loc[100:105, cols]

        b_expect = pd.DataFrame({'FSC-H': {105: 0.25751877, 100: 0.29451752,
                                           101: 0.32627106, 102: 0.42173004},
                                 'CD15 FITC': {105: 0.20802763, 100: 0.20469858,
                                               101: 0.5515328, 102: 0.10146696}}, dtype='float32')
        #np.testing.assert_array_equal(b.loc[:, cols].values, b_expect.loc[:, cols].values)
        np.testing.assert_allclose(b.loc[:, cols].values, b_expect.loc[:, cols].values,
                                   rtol=1e-3,atol=0,err_msg="Results are more different \
                                   than tolerable")
