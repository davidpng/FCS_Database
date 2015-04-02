# -*- coding: utf-8 -*-
"""
Created on Fri 21 Nov 2014 10:59:16 AM PST
This will generate an image file containing the antigens which high comp issues

@author: David Ng, MD
"""
import matplotlib as mplt
mplt.use('Agg')  # Turn off interactive X11 stuff...
import matplotlib.pyplot as plt
import numpy as np

import logging
log = logging.getLogger(__name__)

display_schema = {'comp': {'grid': (9, 4),
                           'size': (12, 20),
                           'plots': {1: {1: (5, 10), 2: (6, 10)},
                                     2: {1: (6, 5), 2: (7, 5), 3: (8, 5), 4: (9, 5)},
                                     3: {1: (7, 6), 2: (8, 6), 3: (9, 6)},
                                     4: {1: (11, 7), 2: (8, 7), 3: (9, 7)},
                                     5: {1: (9, 8), 2: (13, 8)},
                                     6: {1: (14, 9)},
                                     7: {1: (12, 11), 2: (13, 11)},
                                     8: {1: (13, 12), 2: (14, 12)},
                                     9: {1: (14, 13), 4: (4, 14)}}},
                  'M1_gating': {'grid': (2, 6),
                                'size': (16, 6),
                                'plots': {1: {1: (1, 2), 2: (1, 4), 3: (4, 14),
                                              4: (13, 5), 5: (13, 12), 6: (4, 7)},
                                          2: {1: (7, 12), 2: (4, 8), 3: (9, 6),
                                              4: (10, 6), 5: (4, 14), 6: (5, 6)}}}}


class Visualization_2D(object):
    def __init__(self, FCS, outfile, outfiletype, schema_choice='comp', **kwargs):
        self.FCS = FCS
        self.filename = outfile
        self.filetype = outfiletype

        log.info('Plotting %s to %s' % (self.FCS.case_tube, outfile))
        self.display_projection(schema_choice=schema_choice, **kwargs)

    def display_projection(self, schema_choice, **kwargs):
        self.walk_schema(schema=display_schema[schema_choice], **kwargs)
        self.setup_plotting(display_schema[schema_choice])

    def setup_plotting(self, schema, dpi=500):
        fig = plt.gcf()
        fig.set_size_inches(schema['size'][0], schema['size'][1])
        fig.tight_layout()
        fig.savefig(self.filename, dpi=dpi, bbox_inches='tight', filetype=self.filetype)

    def walk_schema(self, schema, **kwargs):
        """
        dict keyed on row, column with value of parameter x, y
        """

        for i, value in schema['plots'].iteritems():
            for j, items in value.iteritems():
                plt.subplot2grid(schema['grid'], (i-1, j-1))
                self.plot_2d_hist(items[0], items[1], **kwargs)

    def plot_2d_hist(self, x, y, cols='b',
                     downsample=None, n_pts=2e4, **kwargs):
        x_lb = self.FCS.parameters.iloc[:, x-1].loc['Channel_Name']
        y_lb = self.FCS.parameters.iloc[:, y-1].loc['Channel_Name']

        if downsample is None:
            n = n_pts
        else:
            n = int(downsample * self.FCS.data.shape[0])
        indices = np.random.choice(range(self.FCS.data.shape[0]), n,
                                   replace=False)

        dat = self.FCS.data.iloc[indices, :]
        x_pts = dat[[x-1]].values
        y_pts = dat[[y-1]].values
        if hasattr(self.FCS, 'cluster') is True:
            cols = self.FCS.cluster[indices]

        plt.scatter(x=x_pts, y=y_pts, s=1,
                    marker='.',
                    c=cols,
                    cmap=mplt.cm.Set1,
                    alpha=0.5, lw=0)
        plt.xlabel(x_lb)
        plt.ylabel(y_lb)
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.xticks([])
        plt.yticks([])

        plt.gca().set_aspect('equal', adjustable='box')

