"""

This is a subroutine for FCS that generates an empty FCS object for export to a database
"""
__author__ = "Daniel Herman, MD"
__copyright__ = "Copyright 2014"
__license__ = "GPL v3"
__version__ = "1.0"
__maintainer__ = "David Ng"
__email__ = "hermands@uw.edu"
__status__ = "Subroutine - prototype"

from os.path import basename
from re import findall
import logging
log = logging.getLogger(__name__)


class empty_FCS(object):
    """ load FCS object for which loadFCS() fails

    Keyword arguments:
    FCS -- FCS object to load to
    filepath -- file to load
    version -- code version to take note of

    Notable attributes:
    .filepath
    .filename
    .case_tube
    .version
    """
    def __init__(self, FCS, error_message, version,
                 filepath=None, **kwargs):

        self.ftype = FCS.ftype

        if self.ftype == 'standard' and 'case_number' in kwargs:
            self.filepath = 'Does not exist'
            self.filename = 'Does not exist'
            self.case_tube = 'Not specified'
            self.case_number = kwargs['case_number']
        elif filepath is not None:
            self.filepath = filepath
            self.filename = basename(filepath)
            if self.ftype == 'standard':
                self.case_tube = self.filename.strip('.fcs')
                self.case_number = self.__filepath_to_case_number()
        else:
            raise ValueError('Making empty FCS object without filepath or case_number')

        self.version = version
        self.error_message = error_message

        if 'flag' in kwargs:
            self.flag = kwargs['flag']

        self.__export(FCS=FCS)

    def __export(self, FCS):
        """ Export loaded parameters to FCS object """
        FCS.filepath = self.filepath
        FCS.filename = self.filename
        FCS.version = self.version
        FCS.empty = True
        FCS.error_message = self.error_message

        if self.ftype == 'standard':
            FCS.case_number = self.case_number
            FCS.case_tube = self.case_tube

        if hasattr(self, 'flag'):
            FCS.flag = self.flag

    def __filepath_to_case_number(self):
        """ Capture case number from filepath

        Gets the HP database number (i.e. ##-#####) from the filepath
        Will ValueError if:
            Filepath does not contain schema
            Filepath schema does not match experiment name schema
        otherwise it will return a database number from either the filepath or experiment name
        """
        file_number = findall(r"\d+.-\d{5}", basename(self.filepath))[0]
        if not file_number:
            raise ValueError("Filepath does not match contain ##-##### schema")
        else:
            return file_number
