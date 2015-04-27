# -*- coding: utf-8 -*-
"""
Created on Wed Sep 17 08:58:06 2014
Finds all fcs files in a given directory and returns the pathnames
@author: ngdavid
"""
import os
import re
import fnmatch
import logging

log = logging.getLogger(__name__)


class Find_Clinical_FCS_Files(object):
    """
    Finds all FCS files matching a pattern NN-NNNNN in a given directory
    """
    def __init__(self, directory=None, Filelist_Path=None, exclude=[], n=None,
                 pattern='[0-9][0-9]-[0-9][0-9][0-9][0-9][0-9]*.fcs',
                 **kwargs):
        """
        if directory ends with .txt we will load the text file as a list
        else if directory will be treated as a directory
        """
        self.directory = directory
        self.excludes = exclude
        self.n_files = n
        self.file_list = Filelist_Path
        self.pattern = pattern

        print('Excluding the following Directories {}'.format(exclude))
        if self.directory is None and \
           self.file_list is not None:
            log.info('Loading filepaths from %s' % self.file_list)
            self.filenames = self.__load_files()
        elif self.directory is not None:
            log.info('Looking for filepaths in directory %s' % self.directory)
            self.filenames = self.__find_files()
            if self.file_list is not None:
                self.write_found_files(self.file_list)
        else:
            raise "Must specify directory or file path"

    def __find_files(self):
        """
        Old Inline (list comprehension style) code:
        filenames = [os.path.join(dirpath, f)
                     for dirpath, dirnames, files in os.walk(self.directory)
                     for f in filter(files, '[0-9][0-9]-[0-9][0-9][0-9][0-9][0-9]*.fcs')]
        """

        # initialization of variables
        filenames = []
        filenum = 0
        filecount = 0

        for dirpath, _, files in os.walk(self.directory, topdown=True):
            # remove sub directories in the exclude list
            if dirpath in self.excludes:
                continue

            filenum += len(files)

            filteredlist = fnmatch.filter(files, self.pattern)
            filecount += len(filteredlist)

            filenames.extend(os.path.join(dirpath, f)
                             for f in filteredlist)

            print "FileCount: {:06d} of {:06d}\r".format(filecount, filenum),

            # update screen/filecount
            if self.n_files is not None and filecount > self.n_files:
                break
        print "\n"

        return filenames

    def __load_files(self):
        with open(self.file_list, 'r') as fo:
            filenames = [filename.strip('\n') for filename in fo]
        return filenames

    def __get_base_folder_name(self, root):
        """
        Performs regex extraction to a XX-XXXXX pattern
        """
        folder_name = os.path.basename(root)
        folder_name = re.findall(r"\d+.-\d{5}", folder_name)
        if folder_name == []:
            folder_name = os.path.basename(root)+' does not match'
            self.make_dict = False
        else:
            folder_name = folder_name[0]
            self.make_dict = True
        return folder_name

    def write_found_files(self, Filelist_Path):
        """
        This will write the found filenames to a text file
        """
        dir_FoundFiles = os.path.join(os.getcwd(), Filelist_Path)

        with open(dir_FoundFiles, 'w+') as fo:
            for f in self.filenames:
                fo.write(f+'\n')
        fo.close()
        print("FCS files found and saved to {}".format(dir_FoundFiles))

if __name__ == '__main__':
    Dir = "/home/ngdavid/Desktop/Ubuntu_Dropbox/Myeloid_Data/Myeloid"

    Finder_obj = Find_Clinical_FCS_Files(Dir)
    print Finder_obj.filenames
