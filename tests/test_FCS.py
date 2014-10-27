"""
Test FCS functions
"""

import logging
from __init__ import TestBase
from FCS_Database.FCS import FCS
from FCS_Database.database.FCS_database import FCSdatabase


log = logging.getLogger(__name__)


class Test_FCS(TestBase):
    def test_FCS_and_FCS_to_DB(self):
        """
        Make a test dataframe, calculate result and then compare it to something
        """
        # Process test data
        filepath = 'adfas'  # fill in
        a = FCS(filepath=filepath, version='test')
        test_db = FCSdatabase(db='test_output/test.db', rebuild=True)
        a.meta_data(db=test_db, add_lists=True)

        # Check database data
        # self.assertEqual(np.around(a.ASCVD[0], 1), results[0])  # example
        # self.assertEqual(np.around(a.ASCVD[1], 1), results[1])  # example
