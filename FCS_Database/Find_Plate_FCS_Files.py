# -*- coding: utf-8 -*-
"""
Created on Wed Sep 17 08:58:06 2014
Finds all fcs files in a given directory and returns the pathnames
@author: ngdavid
"""
import os
import re
from fnmatch import filter


class Find_Plate_FCS_Files(object):
    """
    Finds all FCS files in a given directory
    """
    def __init__(self, directory):
        self.directory = directory
        self.filenames = self.__find_files()

    def __find_files(self):
        filenames = [os.path.join(dirpath, f)
                     for dirpath, dirnames, files in os.walk(self.directory)
                     for f in filter(files, '*.fcs')]
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


if __name__ == '__main__':
    Dir = "/home/ngdavid/Desktop/MDS_Plates/09_27_11_Normal_BM_1"

    Finder_obj = Find_Plate_FCS_Files(Dir)
    print Finder_obj.filenames

