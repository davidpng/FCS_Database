# -*- coding: utf-8 -*-
"""
Created on Mon Oct 27 18:49:11 PDT 2014 
Subroutine to FCS that loads an FCS into memory
@author: ngdavid
"""
__author__ = "David Ng, MD"
__copyright__ = "Copyright 2014, David Ng"
__license__ = "GPL v3"
__version__ = "1.0"
__maintainer__ = "David Ng"
__email__ = "ngdavid@uw.edu"
__status__ = "Production"

"""Installed Packages"""
import numpy as np
import pandas as pd
"""Built in packages"""
from re import compile, findall
from datetime import datetime
from warnings import warn
from struct import calcsize, unpack
from os.path import basename

class loadFCS(object):
    """
    This class loads the information of an FCS file \n
    Internal Variables: \n
    date - <datetime> - Data and time in a python datetime object \n
    filename - <str> - filename \n
    case_number - <str> - case number in ##-##### format extracted from the filepath or \n
                          experiment name \n
    cytometer - <str> - cytometer name \n
    cytnum - <str> - cytometer ID number \n
    num_events - <int> - number of events \n
    channels - <str list> - list of channel names
    parameters - <pandas dataframe> - dataframe containing per channel metainfo
    """
    def __init__(self, FCS, filepath, version, **kwargs):
        """
        Takes an FCS object
        Takes filepath/name
        Takes verion
        
        import_dataframe = True to import listmode as a dataframe
        import_dataframe = False to import listmode as a numpy array
        import_dataframe not included, will just read the header
        """

        # Load raw data
        self.filepath = filepath
        self.fh = open(filepath, 'rb')
        self.header = self.__parse_header()
        self.text = self.__parse_text()
        self.version = version

        # Load processed data
        self.parameters = self.__parameter_header()
        self.channels = self.parameters.loc['Channel Name'].tolist()
        if 'import_dataframe' in kwargs:
            if kwargs['import_dataframe']:
                self.data = pd.DataFrame(self.__parse_data(), columns=self.channels)
            else:
                self.data = self.__parse_data()
        self.date = self.__py_export_time()
        self.filename = self.__get_filename(filepath)
        self.case_number = self.__get_case_number(filepath)
        self.case_tube = self.filename.strip('.fcs')
        self.cytometer, self.cytnum = self.__get_cytometer_info()
        self.num_events = self.__get_num_events()
        self.fh.close()  # not included in FCM package, without it, it leads to a memory leak

        # Export processed data to FCS object
        self.__export(FCS=FCS)

    def __export(self, FCS):
        """ Export loaded parameters to FCS object """
        FCS.parameters = self.parameters
        FCS.date = self.date
        FCS.filepath = self.filepath
        FCS.filename = self.filename
        FCS.cytometer = self.cytometer
        FCS.case_number = self.case_number
        FCS.case_tube = self.case_tube
        FCS.cytnum = self.cytnum
        FCS.num_events = self.num_events
        if hasattr(self, 'data'):
            FCS.data = self.data
        FCS.version = self.version
        return FCS
        
    def __get_case_number(self, filepath):
        """
        Gets the HP database number (i.e. ##-#####) from the filepath and experiment name
        Will ValueError if:
            Filepath does not contain schema
            Filepath schema does not match experiment name schema
        otherwise it will return a database number from either the filepath or experiment name
        """
        file_number = findall(r"\d+.-\d{5}", basename(filepath))
        if self.text.has_key('experiment name'):
            casenum = self.text['experiment name']
            casenum = findall(r"\d+.-\d{5}",casenum) # clean things up to standard
        else:
            casenum = ["Unknown"]

        if not file_number:
            raise ValueError("Filepath does not match contain ##-##### schema")
        if not casenum:
            return file_number[0]
        elif casenum[0] == file_number[0]:
            return casenum[0]
        elif casenum == ["Unknown"]:
            return file_number[0]
        else:
            raise ValueError("Filepath and Experiment Name do not match")

    def __get_filename(self, filepath):
        """Provides error handling in case parameter is undefined"""
        if self.text.has_key('fil'):
            output = self.text['fil']
        else:
            output = basename(filepath)
        return output

    def __get_cytometer_info(self):
        """Provides error handling in case parameter is undefined"""
        if self.text.has_key('cyt'):
            cytometer = self.text['cyt']
        else:
            cytometer = "Unknown"
        if self.text.has_key('cytnum'):
            cytnum = self.text['cytnum']
        else:
            cytnum = "Unknown"
        return cytometer,cytnum

    def __get_num_events(self):
        """if 'tot' is undefined, try to get total number of events from
        __parse_data()
        """
        if self.text.has_key('tot'):
            output = int(self.text['tot'])
        else:
            try:
                output = int(len(self.__parse_data()))
            except:
                raise ValueError("FCS file is corrupted beyond repair: tot and data undefined")
        return output

    def __parse_header(self):
        """
        Parse the FCM data in fcs file at the offset (supporting multiple
        data segments in a file
        """
        header = {}
        header['version'] = float(self.__get_block(3, 5))
        header['text_start'] = int(self.__get_block(10, 17))
        header['text_stop'] = int(self.__get_block(18, 25))
        header['data_start'] = int(self.__get_block(26, 33))
        header['data_end'] = int(self.__get_block(34, 41))
        try:
            header['analysis_start'] = int(self.__get_block(42, 49))
        except ValueError:
            header['analysis_start'] = -1
        try:
            header['analysis_end'] = int(self.__get_block(50, 57))
        except ValueError:
            header['analysis_end'] = -1
        return header

    def __get_block(self, start, stop):
        """Read in bytes from start to stop inclusive."""
        self.fh.seek(start)
        return self.fh.read(stop - start + 1)

    def __parse_data(self):
        """parses the data structure, only listmode float support"""
        start = self.header['data_start']
        end = self.header['data_end']
        datatype = self.text['datatype'].lower()
        mode = self.text['mode'].lower()
        num_events = int(self.text['tot'])
        byteorder = self.text['byteord']
        byteorder_translation = {'4,3,2,1': '>',
                                 '1,2,3,4': '<'} # dictionary to choose byteorder
        if byteorder in byteorder_translation:
            byteorder = byteorder_translation[byteorder]

        if mode != 'l' or datatype != 'f':
            raise ValueError('unsupported mode or datatype')
        else:
            return self.__float_parsing(start, end, datatype, byteorder, num_events)

    def __float_parsing(self, start, end, datatype, byteorder, num_events):
        """
        Parses floating point data given the byte coordinates
        """
        num_items = (end - start + 1) / calcsize(datatype)
        tmp = unpack('%s%d%s' % (byteorder, num_items, datatype), self.__get_block(start, end))
        if len(tmp) % num_events != 0:
            raise IndexError('the byte stream mismatch with number of events')
        return np.array(tmp).reshape((num_events, len(tmp) / num_events))

    def __py_export_time(self):
        if self.text.has_key('export time'):
            export_time = self.text['export time']
        elif self.text.has_key('date') and self.text.has_key('etim'):
            export_time = self.text['date']+'-'+self.text['etim']
        else:
            export_time = '31-DEC-2014-12:00:00'
        return datetime.strptime(export_time,'%d-%b-%Y-%H:%M:%S')

    def __parameter_header(self):
        """
        Generates a dataframe with rows equal to framework and columns
        equal to the number of parameters
        """
        par = int(self.text['par'])  # number of parameters
        framework = [['s','Channel Name'],
                     ['a','Antigen'],
                     ['p','Fluorophore'],
                     ['i','Channel Number'],
                     ['n','Short name'],
                     ['b','Bits'],
                     ['e','Amp type'],
                     ['g','Amp gain'],
                     ['r','Range'],
                     ['v','Voltage'],
                     ['f','Optical Filter Name'],
                     ['l','Excitation Wavelength'],
                     ['o','Excitation Power'],
                     ['t','Detector Type'],
                     ['d','suggested scale']]
        framework = np.array(framework)
        depth = len(framework)
        columns = []
        for i in range(1,par+1):
            columns.append(self.text['p{}n'.format(i)])
        header_df = pd.DataFrame(data=None, index=framework[:,1] ,columns=columns)
        for i in range(1,par+1): #iterate over columns
            for j in range(depth): #iterate over rows
                x = columns[i-1]
                y = framework[j,1]
                if 'p{}{}'.format(i,framework[j,0]) in self.text:
                    if self.text['p{}{}'.format(i,framework[j,0])].isdigit():
                        header_df[x][y] = int(self.text['p{}{}'.format(i,framework[j,0])])
                    else:
                        temp = self.text['p{}{}'.format(i,framework[j,0])]
                        header_df[x][y] = temp.replace('CD ','CD') #handles space after 'CD '
                elif framework[j,0] == 'i':
                    header_df[x][y] = i  # allowance to number the channels
        for i in range(1,par+1):
            x = columns[i-1]
            if pd.isnull(header_df[x]['Channel Name']):
                header_df[x]['Channel Name'] = header_df[x]['Short name']
            parsed_name = header_df[x]['Channel Name'].split(" ", 1)
            if len(parsed_name) == 2:
                header_df[x]['Antigen'] = parsed_name[0]
                header_df[x]['Fluorophore'] = parsed_name[1]
            elif len(parsed_name) == 1:
                header_df[x]['Antigen'] = parsed_name[0]
                header_df[x]['Fluorophore'] = "Unknown"
            else:
                header_df[x]['Antigen'] = "Unknown"
                header_df[x]['Fluorophore'] = "Unknown"

        return header_df

    def __parse_text(self):
        """return parsed text segment of fcs file"""
        start = self.header['text_start']
        stop = self.header['text_stop']
        text = self.__get_block(start, stop)
        delim = text[0]
        if delim == r'|':
            delim = '\|'
        if delim == r'\a'[0]: # test for delimiter being \
            delim = '\\\\' # regex will require it to be \\
        if delim != text[-1]:
            warn("text in segment does not start and end with delimiter")
        tmp = text[1:-1].replace('$', '')
        # match the delimited character unless it's doubled
        regex = compile('(?<=[^%s])%s(?!%s)' % (delim, delim, delim))
        tmp = regex.split(tmp)
        return dict(zip([ x.lower() for x in tmp[::2]], tmp[1::2]))


if __name__ == "__main__":
    filename = "/home/ngdavid/Desktop/Ubuntu_Dropbox/Myeloid_Data/Myeloid/10-13469/10-13469_Myeloid 1.fcs"
    
    class FCS_object(object): 
        """
        Yes, an ass backward way to test this class in isolation but herman 
        made me do it
        """
        def __init__(self):
            self.parameters = 1
            self.date = 1
            self.filepath = 1
            self.filename = 1
            self.cytometer = 1
            self.case_number = 1
            self.case_tube = 1
            self.cytnum = 1
            self.num_events = 1
            if hasattr(self, 'data'):
                self.data = 1
            self.version = 1
            
    FCSobject = FCS_object()
    loadFCS(FCSobject, filename, version = '1a',import_dataframe = False)
    
    print FCSobject.date
    print FCSobject.case_tube
    print FCSobject.data