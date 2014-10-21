# -*- coding: utf-8 -*-
"""
Created on Wed Sep 17 08:58:06 2014
Finds all fcs files in a given directory and returns the pathnames
@author: ngdavid
"""
import os
import re
from fcm import loadFCS
import time
import numpy as np

Dir = "/home/ngdavid/Desktop/Ubuntu_Dropbox/Myeloid_Data/Myeloid"
File_list = '/home/ngdavid/Desktop/Ubuntu_Dropbox/Myeloid_Data/Myeloid/file_list.txt'

class Find_FCS_Files(object):
    """
    """
    def __init__(self,directory,file_list_path):
        self.directory = directory
        self.pattern = pattern
        self.file_list = self._load_file_list(file_list_path)
        #self.search_by_case()
        
    def _load_file_list(self,file_list_path):
        file_list=[]
        file = open(file_list_path,'r')
        for name in file:
            if name.strip() != '':
                file_list.append(name.strip())
        file.close()
        return file_list

    
    def search_by_pattern(self):
        """
        This function will search for all files in a directory that match the 
        given pattern.
        Returns a dictionary of dictionaries containing the
        root/file_list/Tube Type/FCS file location
        """
        output_dict = {}
        for root,dirs,files in os.walk(self.directory):
            folder_name = self.__get_base_folder_name(root)
            fcs_file_names = self.__check_files_match_folder(files,folder_name)
            if self.make_dict:
                output_dict[folder_name] = self.__find_files_match_pattern(root,fcs_file_names)
        return output_dict
        
    def search_by_case(self):
        """
        Given the root directory, file_list_path and patterns, this function will
        Returns a dictionary of dictionaries containing the
        root/file_list/Tube Type/FCS file location
        """        
        output_dict = {}
        for root,dirs,files in os.walk(self.directory):
            folder_name = self.__get_base_folder_name(root)
            if folder_name in self.file_list:
                fcs_file_names = self.__check_files_match_folder(files,folder_name)
                if self.make_dict:
                    output_dict[folder_name] = self.__find_files_match_pattern(root,fcs_file_names)
       
        return output_dict
    def __find_files_match_pattern(self,root,files):
        """
        Returns a dictionary of Pattern and filenames
        """
        output = {}
        for slot in self.pattern:
            for name_type in slot:
                type_file_pairs=[(name_type,_f) for _f in files if name_type.lower() in _f.lower()]
                if len(type_file_pairs)>0 and len(type_file_pairs)<2:
                    output[type_file_pairs[0][0]]=root+'/'+type_file_pairs[0][1]
                elif len(type_file_pairs)>1:
                    #print 'something funky in {}'.format(root)
                    pair_to_use = self.__get_newest_fcs_file(root,type_file_pairs)
                    output[pair_to_use[0]]=root+'/'+pair_to_use[1]
        return output

    def __get_newest_fcs_file(self,root,type_file_pairs):
        """
        find and returns the newest fcs file according to the internal date_stamp
        """
        times = []
        for pair in type_file_pairs:
            file_path = root+'/'+pair[1]
            t = loadFCS(file_path).notes['text']['export time']
            t = t.replace('-',' ')
            t = time.strptime(t,"%d %b %Y %H:%M:%S")
            times.append(t)
        latest_time = max(times)
        latest_index = times.index(latest_time)
        pair_to_use = type_file_pairs[latest_index]
        return pair_to_use
        
            
    def __check_files_match_folder(self,files,folder_name):
        """
        Returns list of fcs files that match the case & folder_name
        """
        output = []
        for _f in files:
            regex = re.escape(folder_name) + r".*.fcs" #regex expression for folder_name*.fcs
            if re.search(regex, _f):
                output.append(_f)
        return output
        
    def __get_base_folder_name(self,root):
        """
        Performs regex extraction to a XX-XXXXX pattern
        """
        folder_name = os.path.basename(root)
        folder_name = re.findall(r"\d+.-\d{5}",folder_name)
        if folder_name == []:
            folder_name = os.path.basename(root)+' does not match'
            self.make_dict=False
        else:
            folder_name = folder_name[0]
            self.make_dict=True
        return folder_name
        

if __name__ == '__main__':
    fcs_obj=Find_FCS_Files(Dir,File_list,Pattern)
    output = fcs_obj.search_by_case()
    output_all =fcs_obj.search_by_pattern()
        