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
from FlowAnal.Analysis_Variables import coords,comp_file,test_fcs_fn
from pandas.util.testing import assert_frame_equal,assert_almost_equal

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

        if write_csv is True:
            write = {}
            write['filepath'] = a.filepath
            write['filename'] = a.filename
            write['case_number'] = a.case_number
            write['cytometer'] = a.cytometer
            write['date'] = a.date
            write['case_tube'] = a.case_tube
            write['num_events'] = a.num_events
            #            write['version'] = a.version
            header_info = pd.Series(write)
            header_info.to_pickle(data('header_info.pkl'))
            a.parameters.to_pickle(data('parameter_info.pkl'))
            log.info('LoadFCS header and Parameter data successfully written')
        else:
            header_info = pd.read_pickle(data('header_info.pkl'))
            self.assertFalse(a.empty)
            self.assertEqual(a.filepath, header_info['filepath'])
            self.assertEqual(a.filename, header_info['filename'])
            self.assertEqual(a.case_number, header_info['case_number'])
            self.assertEqual(a.cytometer, header_info['cytometer'])
            self.assertEqual(a.date, header_info['date'])
            self.assertEqual(a.case_tube, header_info['case_tube'])
            self.assertEqual(a.num_events, header_info['num_events'])
            #            self.assertEqual(a.version, header_info['version'])
            self.assertTrue(hasattr(a, 'data'))

            parameters = pd.read_pickle(data('parameter_info.pkl'))
            assert_frame_equal(a.parameters, parameters)

    def test_feature_extraction(self):
        """ tests ND_Feature_Extraction """
        filepath = data(test_fcs_fn)

        a = FCS(filepath=filepath, import_dataframe=True)
        a.comp_scale_FCS_data(compensation_file=comp_file,
                              gate_coords=coords, rescale_lim=(-0.5,1),
                              strict=False, auto_comp=False)
        a.feature_extraction(extraction_type='FULL', bins=10)

        binned_data = a.FCS_features
        coords = binned_data.Return_Coordinates([1,2,3,4])

        if write_csv:
            coords.to_pickle(data('test_coordinates.pkl'))
            print "Test_coordinates was succefully pickled"
            f = open(data('test_histogram.pkl'),'w')
            pickle.dump(binned_data.histogram,f)
            f.close()
            print "Test histogram was succefully pickled"
        else:
            test_coords = pd.read_pickle(data('test_coordinates.pkl'))
            f = open(data('test_histogram.pkl'),'r')
            test_histogram = pickle.load(f)
            f.close()
            np.testing.assert_allclose(coords.values,test_coords.values)
            np.testing.assert_allclose(binned_data.histogram.data,test_histogram.data)

    def test_2d_feature_extraction(self):
        """ tests 2D_Feature_Extraction """
        
        filepath = data(test_fcs_fn)

        a = FCS(filepath=filepath, import_dataframe=True)
        a.comp_scale_FCS_data(compensation_file=comp_file,
                              gate_coords=coords, rescale_lim=(-0.5,1),
                              strict=False, auto_comp=False)
        a.feature_extraction(extraction_type='2d', bins=50)

        binned_data = a.FCS_features
        print binned_data.histogram
        #coords = binned_data.Return_Coordinates([1,2,3,4])
        """
        if write_csv:
            coords.to_pickle(data('2d_test_coordinates.pkl'))
            print "Test_coordinates was succefully pickled"
            f = open(data('2d_test_histogram.pkl'),'w')
            pickle.dump(binned_data.histogram,f)
            f.close()
            print "Test histogram was succefully pickled"
        else:
            test_coords = pd.read_pickle(data('2d_test_coordinates.pkl'))
            f = open(data('2d_test_histogram.pkl'),'r')
            test_histogram = pickle.load(f)
            f.close()
            np.testing.assert_allclose(coords.values,test_coords.values)
            np.testing.assert_allclose(binned_data.histogram.data,test_histogram.data)
        """
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
        db = FCSdatabase(db=outfile, rebuild=True)
        a.meta_to_db(db=db, dir=root_dir)

        """
        org_file = data('12_00031_db_file.db')
        if 1 == 2: #write_csv:
            db = FCSdatabase(db=org_file, rebuild=True)
            a.meta_to_db(db=db,dir=root_dir)
            print("\nTest Meta Info successfully written\n")
        else:
            db_original = FCSdatabase(db=org_file, rebuild=False)
            db = FCSdatabase(db=outfile, rebuild=True)
            a.meta_to_db(db=db, dir=root_dir)
        """

    def test_comp_vis(self):
        """
        Tests the compensation visualizer subroutine in FCS successfully writes file
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

        outfile = path.join(self.mkoutdir(), 'test_visualization.png')

        a = FCS(filepath=filepath, import_dataframe=True)
        a.comp_scale_FCS_data(compensation_file=comp_file,
                              gate_coords=coords, rescale_lim=(-0.5,1),
                              strict=False, auto_comp=False)

        a.comp_visualize_FCS(outfile=outfile)

    def test_FCS_processing(self):
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

        if write_csv:
            a.data.to_pickle(data('fcs_data.pkl'))
            print("\nProcessed FCS data was successfully pickled\n")
        else:
            comparison_data = pd.read_pickle(data('fcs_data.pkl'))
            np.testing.assert_allclose(a.data.values, comparison_data.values,
                                       rtol=1e-3, atol=0, err_msg="FCS Data results are more \
                                       different than tolerable")

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
                              gate_coords=coords,rescale_lim=(-0.5,1),
                              strict=False, auto_comp=False)
        a.extract_FCS_histostats()

        if write_csv:
            a.PmtStats.to_pickle(data('PmtStats.pkl'))
            pd.Series(a.TubeStats).to_pickle(data('TubeStats.pkl'))
            a.histos.to_pickle(data('histos.pkl'))
            a.comp_correlation.to_pickle(data('comp_correlation.pkl'))
            print("\nHistoStats successfully written\n")
        else:
            PmtStats = pd.read_pickle(data('PmtStats.pkl'))
            TubeStats = pd.read_pickle(data('TubeStats.pkl'))
            histos = pd.read_pickle(data('histos.pkl'))
            comp_correlation = pd.read_pickle(data('comp_correlation.pkl'))

            np.testing.assert_allclose(a.PmtStats.values, PmtStats.values,
                                       rtol=1e-3, atol=0, err_msg="PMT Statistics results are more \
                                       different than tolerable")
            np.testing.assert_allclose(pd.Series(a.TubeStats).values, TubeStats.values,
                                       rtol=1e-3, atol=0, err_msg="Tube Statistics results are more \
                                       different than tolerable")
            np.testing.assert_allclose(a.histos.values, histos.values,
                                       rtol=1e-3, atol=0, err_msg="Histogram results are more \
                                       different than tolerable")
            assert_frame_equal(a.comp_correlation, comp_correlation)

        # log.debug(a.PmtStats)
        # log.debug(a.TubeStats)
        # log.debug(a.histos)
        # log.debug(a.comp_correlation)

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
                                 'CD15 FITC': {105: 0.79197961, 100: 0.79530305,
                                               101: 0.44847226, 102: 0.898543}}, dtype='float32')
        np.testing.assert_allclose(b.loc[:, cols].values, b_expect.loc[:, cols].values,
                                   rtol=1e-3, atol=0, err_msg="Results are more different \
                                   than tolerable")

    def test_add_CustomCaseData(self):
        """ Make sure that CustomCaseData can be loaded

        NOTE: not explicitly checking what is loaded
        """

        root_dir = path.abspath('.')
        outfile = path.join(self.mkoutdir(), 'test.db')
        filename = "12-00031_Myeloid 1.fcs"
        filepath = path.abspath(data(filename))

        a = FCS(filepath=filepath)
        db = FCSdatabase(db=outfile, rebuild=True)
        a.meta_to_db(db=db, dir=root_dir)
        db.addCustomCaseData(file=data('custom_case_data.txt'))

        # Delete other entries
        db.query(delCasesByCustom=True)
        db.close()

        # Need to add query here to check

