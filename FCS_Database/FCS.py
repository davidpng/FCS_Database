# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 18:34:54 2014
Refactorized code from FCM package by Jacob Frelinger for reading just
the FCS header and text information and scrapping FCS metadata

@author: David Ng, MD
"""
"""Installed Packages"""
import numpy as np
import pandas as pd
"""Built in packages"""
from re import compile
from datetime import datetime
from warnings import warn
from struct import calcsize, unpack


class FCS(object):
    """
    This class encapsulates the information of an FCS file \n
    Internal Variables: \n
    date - <datetime> - Data and time in a python datetime object \n
    filename - <str> - filename \n
    cytometer - <str> - cytometer name \n
    cytnum - <str> - cytometer ID number \n
    num_events - <int> - number of events \n
    channels - <str list> - list of channel names
    parameters - <pandas dataframe> - dataframe containing per channel metainfo
    """
    def __init__(self, filename, out_db, **kwargs):
        """
        Takes filename,
        import_dataframe = True to import listmode as a dataframe
        import_dataframe = False to import listmode as a numpy array
        import_dataframe not included, will just read the header
        """
        self.fh = open(filename, 'rb')
        self.header = self.__parse_header()
        self.text = self.__parse_text()
        self.parameters = self.__parameter_header()
        self.channels = self.parameters.loc['Channel Name'].tolist()
        if 'import_dataframe' in kwargs:
            if kwargs['import_dataframe']:
                self.data = pd.DataFrame(self.__parse_data(), columns=self.channels)
            else:
                self.data = self.__parse_data()

        self.date = self.__py_export_time()
        self.filename = self.text['fil']
        self.cytometer = self.text['cyt']
        self.cytnum = self.text['cytnum']
        self.num_events = self.text['tot']
        self.fh.close() # not included in FCM package, without it, it leads to a memory leak
        self.out_db = out_db

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
                                 '1,2,3,4': '<'}
        if byteorder in byteorder_translation:
            byteorder = byteorder_translation[byteorder]

        if mode != 'l' or datatype != 'f':
            raise ValueError('unsupported mode or datatype')
        else:
            return self._float_parsing(start, end, datatype, byteorder, num_events)

    def __float_parsing(self, start, end, datatype, byteorder, num_events):
        """
        Parses floating point data given the byte coordinates
        """
        num_items = (end - start + 1) / calcsize(datatype)
        tmp = unpack('%s%d%s' % (byteorder, num_items, datatype), self._get_block(start, end))
        if len(tmp) % num_events != 0:
            raise IndexError('the byte stream mismatch with number of events')
        return np.array(tmp).reshape((num_events, len(tmp) / num_events))

    def __py_export_time(self):
            export_time = self.text['date']+'-'+self.text['etim']
            return datetime.strptime(export_time,'%d-%b-%Y-%H:%M:%S')

    def __parameter_header(self):
        par = int(self.text['par'])  # number of parameters
        framework = [['s','Channel Name'],
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
        for i in range(1,par+1):
            for j in range(depth):
                x = columns[i-1]
                y = framework[j,1]
                if 'p{}{}'.format(i,framework[j,0]) in self.text:
                    if self.text['p{}{}'.format(i,framework[j,0])].isdigit():
                        header_df[x][y] = int(self.text['p{}{}'.format(i,framework[j,0])])
                    else:
                        temp = self.text['p{}{}'.format(i,framework[j,0])]
                        header_df[x][y] = temp.replace('CD ','CD')
                elif framework[j,0] == 'i':
                    header_df[x][y] = i  # allowance to number the channels
        for i in range(1,par+1):
            x = columns[i-1]
            if pd.isnull(header_df[x]['Channel Name']):
                header_df[x]['Channel Name'] = header_df[x]['Short name']

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

    def meta_to_db(self):
        """ Export meta data to out_db """
        self.export_PmtTubeExp()

    def export_PmtTubeExp(self):
        """ Collect PMT/Tube/Exp specific meta data and send to db """
        d = self.parameters.T
        d['Filename'] = self.filename[:-4]
        self.out_db.add_df(df=d, table='PmtTubeExps')


if __name__ == '__main__':
    filename = '/home/ngdavid/Desktop/MDS_Plates/Inference_Testing/Normal BM backbone_#1.fcs'
    temp = FCS(filename, 'db/test.db')
    print temp.date
    print temp.num_events
    print temp.cytometer
    print temp.channels
    print temp.parameters
