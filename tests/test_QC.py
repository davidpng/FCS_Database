"""
Test FCS QC functions
"""

import logging
from os import path
import numpy as np
import itertools

from __init__ import TestBase, datadir
from FlowAnal.QC_subroutines.Flow_Comparison import calc_emd
log = logging.getLogger(__name__)


def data(fname):
    return path.join(datadir, fname)


class Test_1D_comp(TestBase):
    """ Test FCS subpackage """

    def test_calc_emd(self):
        """ Testing EMD calculation """

        a = np.random.rand(100)

        # Make bins
        bins = np.linspace(0, 100, 100)
        bin_dist = [abs(x[0] - x[1]) for x in itertools.product(bins, repeat=2)]
        bin_dist = np.asarray(bin_dist)
        bin_dist.shape = (100, 100)

        # Identity test
        a_mat = np.append(a, a)
        a_mat.shape = (2, 100)
        score = calc_emd(a_mat, i=0, bin_dist=bin_dist, linear_align=False)
        print "Test of same array: {}".format(score)

        # Addition test #1
        b = a.copy()
        b[40] = b[40] + 1
        a_mat = np.append(a, b)
        a_mat.shape = (2, 100)

        score = calc_emd(a_mat, i=0, bin_dist=bin_dist, linear_align=False)
        print "Test of addition of 1: {}".format(score)

        # Addition test #2
        b = a.copy()
        b[40] = b[40] + 0.1
        a_mat = np.append(a, b)
        a_mat.shape = (2, 100)

        score = calc_emd(a_mat, i=0, bin_dist=bin_dist, linear_align=False)
        print "Test of addition of 0.1: {}".format(score)

        # Shift test #1
        b = a.copy()
        b = np.roll(b, 1)
        a_mat = np.append(a, b)
        a_mat.shape = (2, 100)

        score = calc_emd(a_mat, i=0, bin_dist=bin_dist, linear_align=False)
        print "Test of roll of 1 place: {}".format(score)

        # Shift test #2
        b = a.copy()
        b = np.roll(b, 2)
        a_mat = np.append(a, b)
        a_mat.shape = (2, 100)

        score = calc_emd(a_mat, i=0, bin_dist=bin_dist, linear_align=False)
        print "Test of roll of 2 places: {}".format(score)

        # Addition + Shift test #1
        b = a.copy()
        b[40] = b[40] + 0.1
        b = np.roll(b, 2)
        a_mat = np.append(a, b)
        a_mat.shape = (2, 100)

        score = calc_emd(a_mat, i=0, bin_dist=bin_dist, linear_align=False)
        print "Test of roll of 2 places + add 0.1: {}".format(score)

        # Double random test #1
        b = np.random.rand(100)
        a_mat = np.append(a, b)
        a_mat.shape = (2, 100)

        score = calc_emd(a_mat, i=0, bin_dist=bin_dist, linear_align=False)
        print "Test of two random arrays: {}".format(score)

        # Maximum theoretical distance
        b = np.zeros(100)
        c = np.zeros(100)
        b[0] = 100
        c[99] = 100
        a_mat = np.append(b, c)
        a_mat.shape = (2, 100)
        print a_mat

        score = calc_emd(a_mat, i=0, bin_dist=bin_dist, linear_align=False)
        print "Test of maximum distance: {}".format(score)

        # TODO: as automated comparisons for these tests!!!
        # TODO: change scale so comparable two scale used in flow histograms
