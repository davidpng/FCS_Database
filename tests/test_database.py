"""
Test FCS database functionality
"""

import logging
from os import path
import datetime

from __init__ import TestBase, datadir
from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase

log = logging.getLogger(__name__)


def data(fname):
    return path.join(datadir, fname)


class Test_query_database(TestBase):
    """ Test query of FCS_database objects """

    def test_query_getTubeInfo(self):
        """ Testing querying FCS_database for information """

        root_dir = path.abspath('.')
        outfile = path.join(self.mkoutdir(), 'test.db')
        filename = "12-00031_Myeloid 1.fcs"
        filepath = path.abspath(data(filename))

        a = FCS(filepath=filepath)

        # from FlowAnal.database.FCS_database import FCSdatabase
        db = FCSdatabase(db=outfile, rebuild=True)

        a.meta_to_db(db=db, dir=root_dir)

        # Test specific positive request
        q_dict = {'tubes': ['Myeloid 1'],
                  'daterange': ['2012-01-01', '2012-01-04'],
                  'getTubeInfo': True}
        self.assertEqual(db.query(**q_dict).results,
                         {u'12-00031': {u'Myeloid 1':
                                        {datetime.datetime(2012, 1, 3, 12, 0, 15):
                                         u'testfiles/12-00031_Myeloid 1.fcs'}}})

        # Test specific negative request daterange
        q_dict = {'tubes': ['Myeloid 1'],
                  'daterange': ['2012-01-01', '2012-01-02'],
                  'getTubeInfo': True}
        self.assertEqual(db.query(**q_dict).results,
                         {})

        # Test specific negative request tubes
        q_dict = {'tubes': ['Myeloid 2'],
                  'daterange': ['2012-01-01', '2012-01-04'],
                  'getTubeInfo': True}
        self.assertEqual(db.query(**q_dict).results, {})

    def test_query_getfiles(self):
        """ Testing querying database for getfiles dict_dict """

        root_dir = path.abspath('.')
        outfile = path.join(self.mkoutdir(), 'test.db')
        filename = "12-00031_Myeloid 1.fcs"
        filepath = path.abspath(data(filename))

        a = FCS(filepath=filepath)

        # from FlowAnal.database.FCS_database import FCSdatabase
        db = FCSdatabase(db=outfile, rebuild=True)

        a.meta_to_db(db=db, dir=root_dir)

        # Test specific positive request
        q_dict = {'tubes': ['Myeloid 1'],
                  'daterange': ['2012-01-01', '2012-01-04'],
                  'getfiles': True}
        self.assertEqual(db.query(**q_dict).results,
                         {u'12-00031': {1: u'testfiles/12-00031_Myeloid 1.fcs'}})

        # Test empty query
        q_dict = {'getfiles': True}
        self.assertEqual(db.query(**q_dict).results,
                         {u'12-00031': {1: u'testfiles/12-00031_Myeloid 1.fcs'}})

        # Test case query POS
        q_dict = {'getfiles': True,
                  'cases': ['12-00031']}
        self.assertEqual(db.query(**q_dict).results,
                         {u'12-00031': {1: u'testfiles/12-00031_Myeloid 1.fcs'}})

        # Test case query POS
        q_dict = {'getfiles': True,
                  'cases': ['12-00032']}
        self.assertEqual(db.query(**q_dict).results, {})

        # Test specific negative request daterange
        q_dict = {'tubes': ['Myeloid 1'],
                  'daterange': ['2012-01-01', '2012-01-02'],
                  'getfiles': True}
        self.assertEqual(db.query(**q_dict).results,
                         {})

        # Test specific negative request tubes
        q_dict = {'tubes': ['Myeloid 2'],
                  'daterange': ['2012-01-01', '2012-01-04'],
                  'getfiles': True}
        self.assertEqual(db.query(**q_dict).results, {})
