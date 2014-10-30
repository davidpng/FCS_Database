"""
Test FCS functions
"""

import logging
import os
import sys
   
from __init__ import TestBase
#from FCS_database import FCS
#from FCS_Database.database.FCS_database import FCSdatabase

print sys.path

log = logging.getLogger(__name__)


class Test_FCS(TestBase):
    """ test FCS classes """
    
    def test_loadFCS(self):
        """
        Yes, an ass backward way to test this class in isolation but herman 
        made me do it
        """
        filepath = "../FCS_database/data/12-00031_Myeloid 1.fcs"
        a = FCS(filepath)
     
        print a.date
        print a.case_tube
        print a.data