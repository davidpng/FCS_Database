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

class empty_FCS(object):
    """
    Case to represent and export FCS object meta data for
    files that FCS(f) cannot handle
    """
    def __init__(self, filepath, dirpath, version):
        self.filepath = filepath
        self.filename = basename(filepath)
        self.case_tube = self.filename.strip('.fcs')
        self.dirname = relpath(dirname(filepath), start=dirpath)
        self.case_number = self.filepath_to_case_number()
        self.version = version

    def filepath_to_case_number(self):
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

    def meta_to_db(self, db):
        """ Export meta data to db """
        meta_data = {'filename': self.filename,
                     'case_tube': self.case_tube,
                     'dirname': self.dirname,
                     'case_number': self.case_number,
                     'version': self.version}

        # Push case+tube meta information
        db.add_dict(meta_data, table='TubeCases')

        # Push case
        db.add_list(x=[self.case_number], table='Cases')
