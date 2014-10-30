# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 13:46:51 2014
This class takes list of tubefile names, load, comps and cleans the files and 
performs weighted k-nearest neighbor matching using the first given file
@author: ngdavid
"""

__author__ = "David Ng, MD"
__copyright__ = "Copyright 2014, David Ng"
__license__ = "GPL v3"
__version__ = "0.5"
__maintainer__ = "David Ng"
__email__ = "ngdavid@uw.edu"
__status__ = "Prototyping"

from FCS import FCS
from scipy.spatial import cKDTree
import numpy as np
import pandas as pd
import h5py
import matplotlib.pyplot as plt

class inference_matching(object):
    """
    takes a series of tubes filenames
    and finds common parameters to match cells
    """
    def __init__(self,filelist,comp_file,gate_coords, verbose=False,
                 useless_commons = ['Time','FSC-A','SSC-A','A700-H'],**kwargs):
        """
        Take a lsit of tube filenames as arguements
        Needs compensation matrix and gating coordinates
        TODO: Passing parameters for k - number of nearest neighbors and 
        w - weight scaling for distances
        """
        self._comp_file = comp_file
        self._gate_coords = gate_coords
        self._useless_commons = useless_commons
        self.tube_list = filelist
        
        self.common_antigens = self.__get_common_antigens()  
                
        self.data,self.data_header = self.__push_new_tubes(verbose = verbose)
        
    def __get_common_antigens(self):

        list_of_tube_antigens = []
        for filename in self.tube_list:
            tube = FCS(version = '1')
            tube.load_from_file(filename, version=1, import_dataframe=True)
            antigens = set(tube.data.columns.values.tolist())
            list_of_tube_antigens.append(antigens)
        common_antigens = set.intersection(*list_of_tube_antigens)
        common_antigens = [i for i in common_antigens if i not in self._useless_commons]
        return common_antigens
    
    def __get_target_antigens(self,target):
        temp = set(target.data.columns) - set(self.common_antigens) - set(self._useless_commons)
        return list(temp)
        
    def __find_NN_parameters(self,base,target,k=5,exp_w=2):
        """
        finds the NN given two dataframes base and target
        """
        search_tree = cKDTree(target.data[self.common_antigens])
        dist,indicies = search_tree.query(base.data[self.common_antigens],k=k)
        dist[dist==0] = 1e-20     # condition to avoid division by zero
        weights = (1/dist**exp_w)
        weights = weights/np.sum(weights,axis=1)[:,np.newaxis]
        
        target_antigens = self.__get_target_antigens(target)
        
        antigen_values = []
        for t in target_antigens:
            local_antigen_values = target.data[t].values[indicies]
            antigen_values.append( np.sum(weights*local_antigen_values,axis=1))
        antigen_values = np.array(antigen_values).T
        return pd.DataFrame(data = antigen_values, columns = target_antigens, index = base.data.index)
        
    def __push_new_tubes(self,verbose):
        """
        appends new synthetic columns to the data object
        comp_file and coords will need to be defined as global varaibles
        """
        base = FCS(version = '1')
        base.load_from_file(self.tube_list[0], version=1, import_dataframe=True)
        
        base.comp_scale_FCS_data(compensation_file=self._comp_file,
                                 gate_coords=self._gate_coords,
                                 limits=True,
                                 strict=False)
        output_header = base.parameters
        output = base.data
        
        for filename in self.tube_list[1:]:  # this is embarrasingly parallel
            tube = FCS(version = '1')
            tube.load_from_file(filename, version=1, import_dataframe=True)
            tube.comp_scale_FCS_data(compensation_file=self._comp_file,
                                     gate_coords=self._gate_coords,
                                     limits=True,
                                     strict=False)
            output_to_append = self.__find_NN_parameters(base,tube)
            columns_to_append = output_to_append.columns.tolist()
            if verbose:
                print columns_to_append
            mask = tube.parameters.loc['Channel Name', :].isin(columns_to_append)
            header_to_append = tube.parameters.loc[:, mask]            
            
            output = pd.concat([output,output_to_append],axis = 1)
            output_header = pd.concat([output_header,header_to_append],axis = 1)
        return output,output_header

    def __parallel_worker(self,base,filename):
        tube = FCS(version = '1')
        tube.load_from_file(filename, version=1, import_dataframe=True)
        tube.comp_scale_FCS_data(compensation_file=self._comp_file,
                             gate_coords=self._gate_coords,
                             limits=True,
                             strict=False)
        output_to_append = self.__find_NN_parameters(base,tube)
        columns_to_append = output_to_append.columns.tolist()
        mask = tube.parameters.loc['Channel Name', :].isin(columns_to_append)
        header_to_append = tube.parameters.loc[:, mask]            
        
    def SaveData(self,filename):
        """
        This function saves to an HDF5 datafile:
        The gating parameters
        The parameter headings
        The synthetic dataset 
        """
        output_file = h5py.File(filename,mode='w')
        #gates = output_file.create_group['gates']
        
        param = output_file.create_group['parameters']
        param['index'] = self.data_header.index
        param['columns'] = self.data_header.columns
        param['values'] = self.data_header.values
        data = output_file.create_group['data']
        data['index'] = self.data.index
        data['columns'] = self.data.columns
        data['values'] = self.data.values
        
        return 0

    def InferenceQuality(self,histogram=False,density=True):
        """
        This function calculates the mean and sd of the matched data as well as input data
        """
        # find the mean and sd per matched column
        matched_antigens = self.__get_target_antigens(self)
        if histogram:
            function_hist = lambda x: np.histogram(x,bins=100,range=(0,1),density=True)[0]
            matched_df = np.apply_along_axis(function_hist, 0, self.data[matched_antigens])
            matched_df = pd.DataFrame(matched_df,columns=matched_antigens)
        else:
            matched_df = self.data[matched_antigens].describe()
        # find the mean and sd per input column and make a dataframe
        
        input_df = []
        for filename in self.tube_list:
            tube = FCS(version = '1')
            tube.load_from_file(filename, version=1, import_dataframe=True)
            tube.comp_scale_FCS_data(compensation_file=self._comp_file,
                                 gate_coords=self._gate_coords,
                                 limits=True,
                                 strict=False)            
            target_antigens = self.__get_target_antigens(tube)
            if histogram:
                to_append = np.apply_along_axis(function_hist,0, tube.data[target_antigens])
                to_append = pd.DataFrame(to_append,columns = target_antigens)
            else:
                to_append = tube.data[target_antigens].describe()
            input_df.append(to_append)
        input_df = pd.concat(input_df,axis=1)
        return matched_df, input_df
    
    def PlotInferenceQuality(self,SavetoPDF=False):
        syn_hist,real_hist = self.InferenceQuality(histogram=True,density=True)
        if not set(syn_hist.columns) == set(real_hist.columns):
            raise ValueError("Synthetic and Real data columns do not match")
        for c in syn_hist.columns:
            plt.figure()
            plt.title(c)
            plt.plot(np.arange(0,1,0.01),syn_hist[c],label="Matched/Synthetic Data")
            plt.plot(np.arange(0,1,0.01),syn_hist[c],label="Real/Input Data")
            plt.legend()
        
        
if __name__ == "__main__":
    comp_file = "/home/ngdavid/Desktop/PYTHON/New_Erythroid_Maturation/Erythroid_Maturation/Data/MDSPlateCompLib.txt"

    coords={'singlet': [ (0.01,0.06), (0.60,0.75), (0.93,0.977), (0.988,0.86),
                     (0.456,0.379),(0.05,0.0),(0.0,0.0)],
        'viable': [ (0.358,0.174), (0.609,0.241), (0.822,0.132), (0.989,0.298),
                    (1.0,1.0),(0.5,1.0),(0.358,0.174)]}
    filenames=["/home/ngdavid/Desktop/MDS_Plates/12-02814/Plate 1/12-02814_A1_A01.fcs",
               "/home/ngdavid/Desktop/MDS_Plates/12-02814/Plate 1/12-02814_A2_A02.fcs",
               "/home/ngdavid/Desktop/MDS_Plates/12-02814/Plate 1/12-02814_A3_A03.fcs",
               "/home/ngdavid/Desktop/MDS_Plates/12-02814/Plate 1/12-02814_A4_A04.fcs",
               "/home/ngdavid/Desktop/MDS_Plates/12-02814/Plate 1/12-02814_A5_A05.fcs",
               "/home/ngdavid/Desktop/MDS_Plates/12-02814/Plate 1/12-02814_A6_A06.fcs",
               "/home/ngdavid/Desktop/MDS_Plates/12-02814/Plate 1/12-02814_A7_A07.fcs"]
    
    
    temp = inference_matching(filelist=filenames,comp_file=comp_file,gate_coords=coords,verbose=True)
    print temp.data.columns
    #plot(temp.data['CD1a A647'],temp.data['CD1b A647'],'b,')

    temp.PlotInferenceQuality()