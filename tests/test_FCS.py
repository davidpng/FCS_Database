"""
Test FCS functions
"""

import logging
import warnings
from os import path
import datetime
import numpy as np

from __init__ import TestBase, datadir
from FCS_Database.FCS import FCS
from FCS_Database.database.FCS_database import FCSdatabase

log = logging.getLogger(__name__)


def data(fname):
    return path.join(datadir, fname)


class Test_FCS(TestBase):
    """ Test FCS subpackage """

    def test_loadFCS(self):
        """ Testing loading FCS from file using FCS and loadFCS modules """

        filename = "12-00031_Myeloid 1.fcs"
        filepath = data(filename)
        a = FCS(filepath=filepath)

        self.assertEqual(a.filepath, filepath)
        self.assertEqual(a.filename, filename)
        self.assertEqual(a.case_number, '12-00031')
        self.assertEqual(a.cytometer, 'LSRII - A (LSRII)')
        self.assertEqual(a.date, datetime.datetime(2012, 1, 3, 12, 0, 15))
        self.assertEqual(a.case_tube, '12-00031_Myeloid 1')
        self.assertEqual(a.num_events, 160480)
        self.assertEqual(a.version, 'Blank')

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
        """ Make sure that the push of meta data to db 'runs' """

        root_dir = path.abspath('.')
        outfile = path.join(self.mkoutdir(), 'test.db')
        filename = "12-00031_Myeloid 1.fcs"
        filepath = path.abspath(data(filename))

        a = FCS(filepath=filepath)

        # from FCS_Database.database.FCS_database import FCSdatabase
        db = FCSdatabase(db=outfile, rebuild=True)

        a.meta_to_db(db=db, dir=root_dir)
