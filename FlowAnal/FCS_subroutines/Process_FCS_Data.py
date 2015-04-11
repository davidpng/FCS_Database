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

import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from matplotlib.path import Path
from Auto_Comp_Tweak import Auto_Comp_Tweak
from Auto_Singlet import GMM_doublet_detection

import logging
log = logging.getLogger(__name__)


def Gate_2D(DF_array_data, x_ax, y_ax, coords):
    """
    Returns a logical index given set of gate coordinates
    """
    log.debug('Applying gate coords {} to axes {} and {}'.format(coords, x_ax, y_ax))
    gate = Path(coords, closed=True)
    projection = np.array(DF_array_data[[x_ax, y_ax]])
    index = gate.contains_points(projection)
    return index


def LogicleTransform(input_array, T=2**18, M=4.0, W=1, A=1.0):
    """
    interpolated inverse of the biexponential function

    ul = np.log10(2**18+10000)
    x = np.logspace(0, ul, 10000)
    x = x[::-1] - 400000
    # x = np.arange(-200000, 2**18+10000, 50)
    """
    xn = np.linspace(-2**19, 0, 20000)
    # set up a linear range from -2**19 to zero
    xp = np.logspace(0, np.log10(2**18+10000), 10000)
    # set up a log range from 0 to 2**18+10000
    x = np.concatenate([xn, xp])
    y = BiexponentialFunction(x, T, M, W, A)
    output = interp1d(y.T, x.T, bounds_error=False, fill_value=np.nan)
    return output(input_array)  # NOTE: This fails if values fall outside the defined range


def BiexponentialFunction(input_array, T, M, W, A):
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

    d = rtsafe(w, b)
    if (d < 0) | (d > b):
        raise NameError('d must satisfy 0 < d < b')

    x2 = np.float(A)/np.float(M+A)
    x1 = x2+w
    x0 = x1+w

    c_a = np.exp((b+d)*x0)
    f_a = -np.exp(b*x1)+c_a*np.exp(-d*x1)
    a = T/(np.exp(b)-c_a*np.exp(-d)+f_a)
    f = f_a*a
    c = c_a*a

    return (a*np.e**(b*input_array) - c*np.e**(-d*input_array)+f)


def rtsafe(w, b):
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


class Process_FCS_Data(object):
    """
    This class will compensate and scale data from an .fcs file given an FCSobject and
    spillover library
    Stores a pandas dataframe in data
    Also stores the export_time, cytometer_name, cytometer_num, comp_matrix and tube_name

    rescale_lim - tuple (max,min) for the channels
    strict - switch between strict mode (if channel parameter is undefined, then
             error out) and (if channel parameter is undefined, goto default FL__)

    """

    def __init__(self, FCS, compensation_file, saturation_upper_range=1000,
                 rescale_lim=(-0.15, 1), strict=True, comp_flag = "table",
                 singlet_flag="fixed", viable_flag="fixed", gates1d=[],
                 **kwargs):
        """
        Takes an FCS_object, and a spillover library. \n
        Can handle a spillover library as dictionary if keyed on the machine

        rescale_lim - tuple (min, max) for the channels
        strict - <bool> - default True, strict mode for compensation (if channel
                            parameter is undefined, then error out) and False
                            (if channel parameter is undefined, goto default FL__)
        """
        self.strict = strict
        self.FCS = FCS
        self.FCS.gates = []

        # save columns because data is redfined after comp
        self.columns = self.FCS.parameters.loc['Channel_Name']

        self.FCS.total_events = self.FCS.data.shape[0]   # initial event count

        # Compensate data (or not)
        self.__compensation_switch(comp_mode=comp_flag,
                                   compensation_file=compensation_file,
                                   **kwargs)

        self.data = pd.DataFrame(data=self.data,
                                 columns=self.columns,
                                 dtype=np.float32)  # create a dataframe with columns

        #Saturation Gate might need to go here
        #sat_gate = self._SaturationGate()
        self.data = self._LogicleRescale(T=2**18, M=4, W=0.5, A=0)
        self.FCS.data = self.data  # update FCS.data

        nan_mask = self.__nan_gate(self.data)
        self.data = self.data[nan_mask]

        limit_mask = self.__limit_gate(self.data, high=rescale_lim[1], low=rescale_lim[0])
        self.data = self.data[limit_mask] # this might duplicate the saturation_gate

        self.__Rescale(high=rescale_lim[0], low=rescale_lim[1])  # Edits self.data

        self.__patch() # flips axis so that things display correctly
        self.FCS.data = self.data  # update FCS.data

        if 'gate_coords' in kwargs:   # if gate coord dictionary provided, do initial cleanup
            self.coords = kwargs['gate_coords']
        else:
            self.coords = None

        self.__singlet_switch(singlet_mode=singlet_flag, **kwargs)
        self.__viable_switch(viable_mode=viable_flag, **kwargs)

        # Apply 1D gates
        for gate in gates1d:
            self.__1D_gating(gate)

        self.FCS.data = self.data  # update FCS.data
        del self.data

    def __compensation_switch(self, comp_mode, compensation_file,
                              **kwargs):

        """defines viable gating modes"""
        if comp_mode == 'none':
            self.data = self.FCS.data
        elif comp_mode == "auto":
            Tweaked = Auto_Comp_Tweak(self)
            self.comp_matrix = Tweaked.comp_matrix
            self.data = Tweaked.data
            # data is not compensated at this point!
        elif comp_mode == "table":
            self.overlap_matrix = self._load_overlap_matrix(compensation_file)
            # simple inversion of the overlap matrix
            self.comp_matrix = self._make_comp_matrix(self.overlap_matrix)
            # apply compensation (returns a numpy array)
            self.data = np.dot(self.FCS.data, self.comp_matrix)
        else:
            raise(ValueError,"Compenstation Mode {} is Undefined".format(comp_mode))


    def __singlet_switch(self, singlet_mode, **kwargs):
        """defines singlet gating modes"""
        if singlet_mode == 'none':
            self.FCS.singlet_remain = self.FCS.data.shape[0]
        elif singlet_mode == "auto":
            auto_gate_obj = self.__auto_singlet_gating(**kwargs)
            singlet_mask = auto_gate_obj.singlet_mask
            self.FCS.singlet_remain, percent_loss = auto_gate_obj.calculate_stats()
            self.data = self.data[singlet_mask]
        elif singlet_mode == "fixed" and 'gate_coords' in kwargs:
            singlet_mask = Gate_2D(self.data, 'FSC-A', 'FSC-H',
                                   self.coords['singlet']['coords'])
            self.FCS.singlet_remain = np.sum(singlet_mask)
            self.data = self.data[singlet_mask]
        else:
            raise(ValueError,"Singlet Mode: {} is Undefined".format(singlet_mode))

    def __viable_switch(self, viable_mode, **kwargs):
        """defines viable gating modes"""
        if viable_mode == 'none':
            self.FCS.viable_remain = self.FCS.data.shape[0]
        elif viable_mode == "auto":
            raise(NotImplementedError,"Auto Viability Gating has not been implemented")
        elif viable_mode == "fixed" and 'gate_coords' in kwargs:
            viable_mask = Gate_2D(self.data, 'SSC-H', 'FSC-H',
                                  self.coords['viable']['coords'])
            self.FCS.viable_remain = np.sum(viable_mask)
            self.data = self.data[viable_mask]
        else:
            raise(ValueError,"Viablity Mode: {} is Undefined".format(viable_mode))

    def __auto_singlet_gating(self, **kwargs):
        return GMM_doublet_detection(data=self.data,
                                     filename=self.FCS.filename,
                                     **kwargs)

    def __Clean_up_columns(self, columns):
        """
        Provides error handling and clean up for manually entered parameter names
        !! This should be extraneous !!
        """
        output = [c.replace('CD ', 'CD') for c in columns]
        return output

    def __Rescale(self, high=1.0, low=-0.15,
                  exclude=['FSC-A', 'FSC-H', 'SSC-A', 'SSC-H', 'Time']):
        """This function only modifies a subset of X_input[mask], therefore
        it is better to pass X_input by reference
        """
        mask = ~np.in1d(self.data.columns.values, exclude)
        cols = self.data.columns[mask].values

        self.data[cols] = self.data[cols].apply(func=lambda x:
                                                (x - low) / (high - low), axis=0)

    def __nan_gate(self, X_input):
        """
        limits X_input to all events between 0 and 1
        """
        tmp = X_input.copy()

        for col in tmp.columns:
            tmp[col] = pd.notnull(tmp[col])

        # Tally and record number of cells that are inside of limits
        n_transform_keep = tmp.apply(lambda x: np.sum(x), axis=0)
        n_transform_keep.name = 'transform_not_nan'
        self.FCS.n_transform_not_nan_by_channel = n_transform_keep

        # True if all true (Not sure if this is fastest)
        mask = np.prod(tmp, axis=1).astype(bool)
        self.FCS.n_transform_not_nan_all = np.sum(mask)

        return mask

    def __limit_gate(self, X_input, high, low):
        """
        limits X_input to all events between 0 and 1
        """
        tmp = X_input.drop(['Time'], axis=1).copy()
        reagents = [x for x in tmp.columns.values
                    if x not in ['FSC-A', 'FSC-H', 'SSC-A', 'SSC-H']]

        for col in tmp.columns:
            if col in reagents:
                tmp[col] = (tmp[col] <= high) & (tmp[col] >= low)
            else:
                tmp[col] = (tmp[col] <= 1) & (tmp[col] >= 0)

        # Tally and record number of cells that are inside of limits
        n_transform_keep = tmp.apply(lambda x: np.sum(x), axis=0)
        n_transform_keep.name = 'transform_in_limits'
        self.FCS.n_transform_keep_by_channel = n_transform_keep

        # True if all true (Not sure if this is fastest)
        mask = np.prod(tmp, axis=1).astype(bool)
        self.FCS.n_transform_keep_all = np.sum(mask)

        return mask

    def _load_overlap_matrix(self, compensation_file):
        """
        Loads the the spectral overlap library and returns spectral overlap matrix
        Pass compensation_file as a dictionary if there are different spectral
        overlap libaries for difference cytometers
        """
        columns = list(self.columns)
        if isinstance(compensation_file, str):
            spectral_overlap_file = compensation_file
        elif isinstance(compensation_file, dict):
            if self.FCS.cytnum in compensation_file.keys():
                spectral_overlap_file = compensation_file[self.FCS.cytnum]
            else:
                raise ValueError('Cytometer ' + self.cytnum +
                                 'is not seen in the compensation dictionary')
        else:
            raise TypeError('Provided compensation_file is not of type str or dict')
        spectral_overlap_library = pd.read_table(spectral_overlap_file, comment='#', sep='\t',
                                                 header=0, index_col=0).dropna(axis=0, how='all')
        Undescribed = set(columns)-set(spectral_overlap_library.columns)
        if Undescribed:
            if self.strict:  # if strict == true, then error out with Undescrbied antigens
                raise IOError('Antigens: ' + ','.join(Undescribed) + ' are not described in the library')
            else:  #try to fix by replacing with defaults (be careful!, these spillovers might not work well)
                Defaults = ['FSC-A', 'FSC-H', 'SSC-A', 'SSC-H', 'FL01', 'FL02', 'FL03',
                            'FL04', 'FL05', 'FL06', 'FL07', 'FL08', 'FL09', 'FL10', 'Time']
                for ukn in Undescribed:
                    i = columns.index(ukn)
                    columns[i] = Defaults[i]
        else:
            pass    # Undescribed is an empty set and we can use columns directly

        overlap_matrix = spectral_overlap_library[columns].values   # create a matrix from columns
        return overlap_matrix.T

    def _make_comp_matrix(self, overlap_matrix):
        """
        Generates a compensation matrix given a spectral overlap matrix
        Provides error handling for ill-poised overlap matrices
        TODO: Make sure all values in overlap matrix are less than 1
        i.e. can't have more than 100% comp or spillover
        """
        if overlap_matrix.shape[0] != overlap_matrix.shape[1]:  # check to make sure matrix is invertable
            raise ValueError('spectral overlap matrix is not square')
        if overlap_matrix.shape[0] != np.trace(overlap_matrix):
            print overlap_matrix
            raise ValueError('Diagonals of the spectral overlap matrix are not one')
        if not np.isfinite(np.linalg.cond(overlap_matrix)):
            print overlap_matrix
            raise ValueError('matrix is not invertable')
        else:
            return np.linalg.inv(overlap_matrix)

    def _SaturationGate(self, X_input, limit, exclude=['Time', 'time']):
        """
        Finds values between zero AND greater than 2^18-'limit'
        mask defines the columns where we will look for these values (typically exclude 'time')
        N.B. Best to apply this after compensation
        """
        mask = [x for x in X_input.columns.values if x not in exclude]
        lower_limit = np.any(X_input[mask] <= -75000, axis=1)  # find events with compensated params <=1 (because log10(1)=0)
        lim = 2**18-limit
        upper_limit = np.any(X_input[mask] > lim, axis=1)  # fine events with compensated params >max less 1000
        return np.logical_not(np.logical_or(lower_limit, upper_limit))

    def __1D_gating(self, gate):
        """ Applys 1D specified by  given parameter/comparator/limit """

        (axis, comparator, limit) = gate.split(' ')
        log.debug('Applying gating {} {} {}'.format(axis, comparator, limit))
        if comparator == '>':
            mask = self.data[axis] > float(limit)
        elif comparator == '<':
            mask = self.data[axis] < float(limit)
        else:
            raise ValueError('{} is not a valid comparator'.format(comparator))

        self.FCS.gates.append(("_".join([axis, comparator, limit]), np.sum(mask)))

        self.data = self.data.loc[mask, :]

    def _LogicleRescale(self, lin=['FSC-A', 'FSC-H'],
                        T=2**18, M=4.0, W=1, A=0, max_val=2**18,
                        **kwargs):
        """
        Applies logicle transformation to columns defined by log_mask
        Applies rescaling from [0,1) to columns defined on rescale_mask
        Operates pass-by-reference (i.e. in place)
        *log_param = passes parameters to be logicle transformed
        """
        if 'log_param' in kwargs:
            log = kwargs.get("log_param")
        else:
            log = [x for x in self.data.columns.values
                   if x not in lin + ['Time']]

        output = self.data.copy()

        # logicle transform and rescaling
        output[log] = LogicleTransform(self.data[log].values, T, M, W, A) / np.float(max_val)

        output[lin] = self.data[lin].values / np.float(max_val)  # rescale forward scatter linear

        return output

    def __LogicleTransform(self, input_array, T=2**18, M=4.0, W=1, A=1.0):
        """
        interpolated inverse of the biexponential function

        ul = np.log10(2**18+10000)
        x = np.logspace(0, ul, 10000)
        x = x[::-1] - 400000
        # x = np.arange(-200000, 2**18+10000, 50)
        """
        xn = np.linspace(-2**19, 0, 20000)
        #set up a linear range from -2**19 to zero
        xp = np.logspace(0, np.log10(2**18+10000), 10000)
        #set up a log range from 0 to 2**18+10000
        x = np.concatenate([xn, xp])
        y = self.__BiexponentialFunction(x, T, M, W, A)
        output = interp1d(y.T, x.T, bounds_error=False, fill_value=np.nan)
        return output(input_array)  # NOTE: This fails if values fall outside the defined range

    def __rtsafe(self, w, b):
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

    def __BiexponentialFunction(self, input_array, T, M, W, A):
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

        d = self.__rtsafe(w, b)
        if (d < 0) | (d > b):
            raise NameError('d must satisfy 0 < d < b')

        x2 = np.float(A)/np.float(M+A)
        x1 = x2+w
        x0 = x1+w

        c_a = np.exp((b+d)*x0)
        f_a = -np.exp(b*x1)+c_a*np.exp(-d*x1)
        a = T/(np.exp(b)-c_a*np.exp(-d)+f_a)
        f = f_a*a
        c = c_a*a

        return (a*np.e**(b*input_array) - c*np.e**(-d*input_array)+f)

    def __patch(self):
        """
        This function is a temporary patch that flips the flurophore parameters of self.data
        """
        mask = [x for x in self.data.columns
                if x not in ['FSC-A', 'FSC-H', 'SSC-A', 'SSC-H', 'Time']]
        #print "the mask is :"
        #print mask
        #print self.data[mask]
        self.data[mask] = 1-self.data[mask]

if __name__ == "__main__":
    import os
    import sys

    cwd = os.path.dirname(__file__)
    parent =  os.path.realpath('..')
    root = os.path.realpath('../..')
    sys.path.insert(0,parent)
    from FlowAnal.FCS import FCS
    from os import path
    datadir = "/home/ngdavid/Desktop/PYTHON/FCS_File_Database/testfiles"

    def data(fname):
        return path.join(datadir, fname)


    coords={'singlet': [ (0.01,0.06), (0.60,0.75), (0.93,0.977), (0.988,0.86),
                         (0.456,0.379),(0.05,0.0),(0.0,0.0)],
            'viable': [ (0.358,0.174), (0.609,0.241), (0.822,0.132), (0.989,0.298),
                        (1.0,1.0),(0.5,1.0),(0.358,0.174)]}

    comp_file={'H0152':root+'/FlowAnal/data/Spectral_Overlap_Lib_LSRA.txt',
               '2':root+'/FlowAnal/data/Spectral_Overlap_Lib_LSRB.txt'}

    filename = "12-00031_Myeloid 1.fcs"
    filepath = data(filename)

    FCS_obj = FCS(filepath=filepath, import_dataframe=True)

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
"""
    filename = "12-00005_Bone Marrow WBC.fcs"
    filepath = data(filename)

    FCS_obj = FCS(filepath=filename,import_dataframe=True)

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

"""
