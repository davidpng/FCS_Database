# -*- coding: utf-8 -*-
"""
Created on Wed Sep 17 08:58:06 2014
Finds all fcs files in a given directory and returns the pathnames
@author: ngdavid
"""
import os
import re
import fnmatch

class Find_Clinical_FCS_Files(object):
    """
    Finds all FCS files matching a pattern NN-NNNNN in a given directory
    """
    def __init__(self, directory,exclude=[],**kwargs):
        """
        if directory ends with .txt we will load the text file as a list
        else if directory will be treated as a directory
        """
        self.directory = directory
        self.excludes = exclude
        print('Excluding the following Directories {}'.format(exclude))
        if '.txt' in self.directory:
            self.filenames = self.__load_files()
        else:
            self.filenames = self.__find_files()
            if "Filelist_Path" in kwargs:
                # do only if Filelist_Path included and directory is not a txt
                # file
                self.write_found_files(kwargs['Filelist_Path'])

    def __find_files(self):
        """
        Old Inline (list comprehension style) code:
        filenames = [os.path.join(dirpath, f)
                     for dirpath, dirnames, files in os.walk(self.directory)
                     for f in filter(files, '[0-9][0-9]-[0-9][0-9][0-9][0-9][0-9]*.fcs')]
        """
        #initialization of variables
        filenames = []
        filenum = 0
        filecount = 0
        #find all directories in given self.directory
        sub_directories=os.listdir(self.directory)
        #remove sub directories in the exclude list
        sub_directories = list(set(sub_directories)-set(self.excludes))
        print("Sub-directories to be searched: {}".format(sub_directories))
        for sub_dirs in sub_directories:
            #search individual sub_directories
            for dirpath,dirnames,files in os.walk(os.path.join(self.directory,sub_dirs)):
                #for files that match the XX-XXXXX pattern
                filteredlist = fnmatch.filter(files,'[0-9][0-9]-[0-9][0-9][0-9][0-9][0-9]*.fcs')
                filenum+=len(files)
                for f in filteredlist:
                    #and add it to the filenames list
                    filenames.append(os.path.join(dirpath,f))
                    filecount+=1
                    #then update the status count
                    print("FileCount: {:06d} of {:06d}\r".format(filecount,filenum)),
                print("FileCount: {:06d} of {:06d}\r".format(filecount,filenum)),
                #update screen/filecount
        return filenames

    def __load_files(self):
        with open(self.directory,'r') as fo:
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

    def write_found_files(self,Filelist_Path):
        """
        This will write the found filenames to a text file
        """
        dir_FoundFiles = os.path.join(os.getcwd(),Filelist_Path)

        with open(dir_FoundFiles,'w+') as fo:
            for f in self.filenames:
                fo.write(f+'\n')
        fo.close()
        print("FCS files found and saved to {}".format(dir_FoundFiles))

if __name__ == '__main__':
    Dir = "/home/ngdavid/Desktop/Ubuntu_Dropbox/Myeloid_Data/Myeloid"

    Finder_obj = Find_Clinical_FCS_Files(Dir)
    print Finder_obj.filenames

