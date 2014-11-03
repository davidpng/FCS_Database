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


class empty_FCS(object):
    """
    Case to represent and export FCS object meta data for
    files that FCS(f) cannot handle
    """
    def __init__(self, FCS, filepath, version, **kwargs):
        self.filepath = filepath
        self.filename = basename(filepath)
        self.case_tube = self.filename.strip('.fcs')
        self.case_number = self.__filepath_to_case_number()
        self.version = version
        self.__export(FCS=FCS)

    def __export(self, FCS):
        """ Export loaded parameters to FCS object """
        FCS.filepath = self.filepath
        FCS.filename = self.filename
        FCS.case_number = self.case_number
        FCS.case_tube = self.case_tube
        FCS.version = self.version
        FCS.empty = True

    def __filepath_to_case_number(self):
        """
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
