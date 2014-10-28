# -*- coding: utf-8 -*-
"""
Created on Fri Oct 24 15:03:23 2014
Provides Compensation and scaling functionality
@author: ngdavid
"""

__author__ = "David Ng, MD"
__copyright__ = "Copyright 2014, David Ng"
__license__ = "GPL v3"
__version__ = "1.0"
__maintainer__ = "David Ng"
__email__ = "ngdavid@uw.edu"
__status__ = "Production"

import re
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from matplotlib.path import Path

class Process_FCS_Data(object):
    """
    This class will compensate and scale an FCS file given an FCSobject and
    spillover library
    Stores a pandas dataframe in data
    Also stores the export_time, cytometer_name, cytometer_num, comp_matrix and tube_name

    rescale_lim - tuple (max,min) for the channels
    limits - applies rescale limits
    strict - switch between strict mode (if channel parameter is undefined, then
             error out) and (if channel parameter is undefined, goto default FL__)

    """

    def __init__(self, FCS, compensation_file, saturation_upper_range=1000,
                 rescale_lim=(-0.15, 1), limits=False, strict=True, **kwargs):
        """
        Takes an FCS_object, and a spillover library. \n
        Can handle a spillover library as dictionary if keyed on the machine

        rescale_lim - tuple (min, max) for the channels
        limits - <bool> - default False, applies rescale limits \n
        strict - <bool> - default True, strict mode for compensation (if channel
                            parameter is undefined, then error out) and False
                            (if channel parameter is undefined, goto default FL__)

        """
        self.strict = strict
        self.FCS = FCS
        self.columns = self.__Clean_up_columns(self.FCS.parameters.loc['Channel Name'])         # save columns because data is redfined after comp
        self.total_events = self.FCS.data.shape[0]      #initial number of events before gating
        pattern = re.compile("new", re.IGNORECASE)
        self.comp_matrix = self._load_comp_matrix(compensation_file)    # load compensation matrix
        self.data = np.dot(self.FCS.data, self.comp_matrix)             # apply compensation (returns a numpy array)
        self.data = pd.DataFrame(data=self.data[:,:], \
                                 columns=self.columns, \
                                 dtype=np.float32) # create a dataframe with columns
        
        self.data = self._LogicleRescale(self.data, T=2**18, M=4, W=0.5, A=0)
        self.FCS.data = self.data # update FCS.data
        
        if limits==True:
            limit_mask = self.__limit_gate(self.data,high=rescale_lim[1], low=rescale_lim[0])
            self.data = self.data[limit_mask]
            self.__Rescale(self.data, high=rescale_lim[0], low=rescale_lim[1]) #self.data is modified
            self.FCS.data = self.data # update FCS.data
            
        if kwargs.has_key('gate_coords'):   # if gate coord dictionary provided, do initial cleanup
            coords = kwargs['gate_coords']
            self.coords = coords
            if coords.has_key('viable'):
                viable_mask = self.__gating(self.data, 'SSC-H', 'FSC-H', coords['viable'])
                self.data = self.data[viable_mask]
            if coords.has_key('singlet'):
                singlet_mask = self.__gating(self.data, 'FSC-A', 'FSC-H', coords['singlet'])
                self.data = self.data[singlet_mask]
        else:
            self.coords = None
        self.FCS.data = self.data # update FCS.dat
        

    def __Clean_up_columns(self, columns):
        """
        Provides error handling and clean up for manually entered parameter names
        """
        output = [c.replace('CD ','CD') for c in columns]
        return output

    def __Rescale(self, X_input, high=1, low=-0.15, \
                  exclude=['FSC-A','FSC-H','SSC-A','SSC-H','Time']):
        """This function only modifies a subset of X_input[mask], therefore
        it is better to pass X_input by reference
        """
        mask = [x for x in X_input.columns.values if x not in exclude]
        X_input[mask] = (X_input[mask]-low)/(high-low)

    def __limit_gate(self,X_input,high,low):
        """
        limits X_input to all events between 0 and 1
        """
        mask = [x for x in X_input.columns.values if x not in ['FSC-A','FSC-H','SSC-A','SSC-H','Time']]
        upper = np.all(X_input[mask]<=high,axis=1)
        lower = np.all(X_input[mask]>=low,axis=1)
        mask = ['FSC-A','FSC-H','SSC-A','SSC-H']
        upper1 = np.all(X_input[mask]<=1,axis=1)
        lower1 = np.all(X_input[mask]>=0,axis=1)
        return upper*lower*upper1*lower1

    def _load_comp_matrix(self, compensation_file):
        """
        Loads the the spectral overlap library and returns compensation matrix
        Pass compensation_file as a dictionary if there are different spectral
        overlap libaries for difference cytometers
        """
        columns = list(self.columns)
        if isinstance(compensation_file,str):
            spectral_overlap_file = compensation_file
        elif isinstance(compensation_file,dict):
            if self.FCS.cytnum in compensation_file.keys():
                spectral_overlap_file = compensation_file[self.FCS.cytnum]
            else:
                raise ValueError('Cytometer '+ self.cytometer_num + \
                                 'is not seen in the compensation dictionary')
        else:
            raise TypeError('Provided compensation_file is not of type str or dict')
        spectral_overlap_library = pd.read_table(spectral_overlap_file,comment='#',sep='\t',
                                             header=0,index_col=0).dropna(axis=0,how='all')
        Undescribed = set(columns)-set(spectral_overlap_library.columns)
        if Undescribed:
            if self.strict: #if strict == true, then error out with Undescrbied antigens
                raise IOError('Antigens: '+','.join(Undescribed)+' are not described in the library')
            else:  #try to fix by replacing with defaults (be careful!, these spillovers might not work well)
                Defaults = ['FSC-A', 'FSC-H', 'SSC-A', 'SSC-H', 'FL01', 'FL02', 'FL03',\
                        'FL04', 'FL05', 'FL06', 'FL07', 'FL08', 'FL09', 'FL10', 'Time']
                for ukn in Undescribed:
                    i = columns.index(ukn)
                    columns[i] = Defaults[i]
        else:
            pass    # Undescribed is an empty set and we can use columns directly

        overlap_matrix = spectral_overlap_library[columns].values   #create a matrix from columns

        if overlap_matrix.shape[0] != overlap_matrix.shape[1]:      #check to make sure matrix is invertable
            raise ValueError('spectral overlap matrix is not square')
        if overlap_matrix.shape[0] != np.trace(overlap_matrix):
            print overlap_matrix
            raise ValueError('Diagonals of the spectral overlap matrix are not one')

        if not np.isfinite(np.linalg.cond(overlap_matrix.T)):
            print overlap_matrix.T
            raise ValueError('matrix is not invertable')
        else:
            return np.linalg.inv(overlap_matrix.T)

    def _SaturationGate(self, X_input, limit, exclude=['Time','time']):
        """
        Finds values between zero AND greater than 2^18-'limit'
        mask defines the columns where we will look for these values (typically exclude 'time')
        N.B. Best to apply this after compensation
        """
        mask = [x for x in X_input.columns.values if x not in exclude]
        lower_limit = np.any(X_input[mask]<=-75000, axis=1) #find events with compensated params <=1 (because log10(1)=0)
        lim = 2**18-limit
        upper_limit = np.any(X_input[mask]>lim, axis=1) #fine events with compensated params >max less 1000
        return np.logical_not(np.logical_or(lower_limit, upper_limit))

    def __gating(self, DF_array_data, x_ax, y_ax, coords):
        """
        Returns a logical index given set of gate coordinates
        """
        gate = Path(coords, closed=True)
        projection = np.array(DF_array_data[[x_ax, y_ax]])
        index = gate.contains_points(projection)
        return index

    def _LogicleRescale(self, X_input,lin=['FSC-A','FSC-H'],
                        T=2**18, M=4.0, W=1, A=0,**kwargs):
        """
        Applies logicle transformation to columns defined by log_mask
        Applies rescaling from [0,1) to columns defined on rescale_mask
        Operates pass-by-reference (i.e. in place)
        *log_param = passes parameters to be logicle transformed
        """
        if kwargs.has_key("log_param"):
            log = kwargs.get("log_param")
        else:
            log = [x for x in X_input.columns.values if x not in lin + ['Time']]
        output = X_input.copy()
        output[log] = self.__LogicleTransform(X_input[log].values,T, M, W, A)/np.float(2**18) #logicle transform and rescaling
        output[lin] = X_input[lin].values/(2**18) #rescale forward scatter linear

        return output

    def __LogicleTransform(self, input_array, T=2**18, M=4.0, W=1, A=1.0):
        """
        interpolated inverse of the biexponential function
        """
        ul = np.log10(2**18+10000+400000)
        x = np.logspace(0,ul,10000)
        x = x[::-1] - 400000
        #x=np.arange(-200000,2**18+10000,50)

        y=self.__BiexponentialFunction(x,T,M,W,A)
        output=interp1d(y.T,x.T)
        return output(input_array)

    def __rtsafe(self,w,b):
        """
        Modified from 'Numerical recipes: the art of scientific computing'
        solves the following equation for d : w = 2ln(d/b) / (b+d)
        where d = (0,b)
        """

        #the functions
        def gFunction(d):                           #This defines the function we are 'rooting' for
            return (w*(b+d) + 2*(np.log(d)-np.log(b)))
        def derivFunction(d):                       #Derivative of g
            return (w+2/d)

        X_ACCURACY = 0.0000001
        MAX_IT = 1000

        lowerLimit = 0.0  #defines upper and lower limits where to find the roots
        upperLimit = np.float(b)

        if ((gFunction(lowerLimit)>0) & (gFunction(upperLimit)>0)) | ((gFunction(lowerLimit)<0) & (gFunction(upperLimit)<0)):
            raise NameError('Root must be bracketed') # if the f(d) at both ends have the same sign, there is no root

        if gFunction(lowerLimit)<0:
            xLow = lowerLimit
            xHigh = upperLimit
        else:
            xLow = upperLimit
            xHigh = lowerLimit

        root = np.float(lowerLimit + upperLimit)/2      #sets the intial guess for root at midpoint
        dxOld = np.abs(upperLimit - lowerLimit)    #differenance from previous guess
        dx = dxOld                              #no reason - define dx just in case
        g = gFunction(root)                     #intitial function value at root_0
        dg = derivFunction(root)                #intial derivative value at root_0

        for i in range(0,MAX_IT):
            if (((root-xHigh)*dg-g)*((root-xLow)*dg-g) > 0)|(abs(2*g) > abs(dxOld*dg)):
                #Bisect method
                dxOld = dx
                dx = (xHigh-xLow)/2
                root = xLow + dx
            else:
                #Newton method
                dxOld = dx
                dx = g/dg
                root = root - dx

            if (abs(dx) < X_ACCURACY):
                return root #stop condition and return root

            g = gFunction(root)         #reinitialize g to new root
            dg = derivFunction(root)    #reinitialize dg to new derivative

            if g < 0: #move the xLow or xHigh to the new search area
                xLow = root
            else:
                xHigh = root

    def __BiexponentialFunction(self,input_array, T, M, W, A):
        """
        LOGICLE performs logicle transform of flow data
            T = top of scale data
            M = total plot width in asymptotic decades
            W = width of linearization                              = 3
           A = number of additional decades of negative data values =0

        This function references: Moore, W et al. "Update for the Logicle Data Scale Including
        Operational Code Implementation" Cytometry Part A. 81A 273-277, 2012
        """
        input_array = input_array/float(T)

        b = (M+A)*np.log(10)
        w = np.float(W)/np.float(M+A)

        d = self.__rtsafe(w,b)
        if (d<0) | (d>b):
            raise NameError('d must satisfy 0 < d < b')

        x2 = np.float(A)/np.float(M+A)
        x1 = x2+w
        x0 = x1+w

        c_a = np.exp((b+d)*x0)
        f_a = -np.exp(b*x1)+c_a*np.exp(-d*x1)
        a = T/(np.exp(b)-c_a*np.exp(-d)+f_a)
        f = f_a*a
        c = c_a*a

        return (a*np.e**(b*input_array)-c*np.e**(-d*input_array)+f)



if __name__ == "__main__":
    import os
    import sys
   
    cwd = os.path.dirname(__file__)
    parent =  os.path.realpath('..')
    root = os.path.realpath('../..')
    sys.path.insert(0,parent)
    from FCS import FCS
    coords={'singlet': [ (0.01,0.06), (0.60,0.75), (0.93,0.977), (0.988,0.86),
                         (0.456,0.379),(0.05,0.0),(0.0,0.0)],
            'viable': [ (0.358,0.174), (0.609,0.241), (0.822,0.132), (0.989,0.298),
                        (1.0,1.0),(0.5,1.0),(0.358,0.174)]}
    
    comp_file={'H0152':root+'/FCS_Database/data/Spectral_Overlap_Lib_LSRA.txt',
               '2':root+'/FCS_Database/data/Spectral_Overlap_Lib_LSRB.txt'}

    filename = root + "/FCS_Database/data/12-00031_Myeloid 1.fcs"

    FCS_obj = FCS(version = '1.2',filepath=filename,import_dataframe=True)
    
    FCS_obj.comp_scale_FCS_data(compensation_file=comp_file,
                            gate_coords=coords,
                            strict=False)
    
    figure()
    ax=['SSC-H','CD45 APC-H7']
    plot(FCS_obj.data[ax[0]],FCS_obj.data[ax[1]],'b,')
    title(FCS_obj.case_tube)
    xlim(0,1)
    ylim(0,1)
    xlabel(ax[0])
    ylabel(ax[1])
    
    filename = root + "/FCS_Database/data/12-00005_Bone Marrow WBC.fcs"
    FCS_obj = FCS(version = '1.2',filepath=filename,import_dataframe=True)
    
    FCS_obj.comp_scale_FCS_data(compensation_file=comp_file,
                            gate_coords=coords,
                            strict=False)
   
    figure()
    ax=['SSC-H','CD45 V450']
    plot(FCS_obj.data[ax[0]],FCS_obj.data[ax[1]],'b,')
    title(FCS_obj.case_tube)
    xlim(0,1)
    ylim(0,1)
    xlabel(ax[0])
    ylabel(ax[1])
    