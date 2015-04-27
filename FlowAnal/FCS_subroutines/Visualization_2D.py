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
                                     9: {1: (14, 13), 4: (4, 14)}},
                           'lim': (0, 1, 0, 1)},
                  'M1_gating': {'grid': (2, 6),
                                'size': (16, 6),
                                'plots': {1: {1: (1, 2), 2: (1, 4), 3: (4, 14),
                                              4: (13, 5), 5: (13, 12), 6: (4, 7)},
                                          2: {1: (7, 12), 2: (4, 8), 3: (9, 6),
                                              4: (10, 6), 5: (4, 14), 6: (5, 6)}},
                                'lim': (0, 1, 0, 1)},
                  'SingleAntigen': {'grid': (2, 10),
                                    'size': (16, 5),
                                    'plots': None,
                                    'lim': None}}


class Visualization_2D(object):
    def __init__(self, FCS, outfile, outfiletype,
                 schema_choice='comp', comp_lines=[], gate=None, **kwargs):
        self.FCS = FCS
        self.filename = outfile
        self.filetype = outfiletype
        self.comp_lines = comp_lines
        self.gate = gate

        log.info('Plotting %s to %s' % (self.FCS.filepath, outfile))
        self.display_projection(schema_choice=schema_choice, **kwargs)

    def display_projection(self, schema_choice, **kwargs):
        self.make_plot_schema(schema_choice, **kwargs)
        self.walk_schema(schema=display_schema[schema_choice], **kwargs)
        self.setup_plotting(display_schema[schema_choice])

    def make_plot_schema(self, schema_choice, **kwargs):
        if schema_choice == 'SingleAntigen':
            tmp = {1: {x: (x+4, kwargs['col_i']+1)
                       for x in range(1, 11)},
                   2: {1: (1, 2), 2: (4, 1),
                       3: (1, kwargs['col_i']+1), 4: (4, kwargs['col_i']+1)}}
            display_schema[schema_choice]['plots'] = tmp

    def setup_plotting(self, schema, dpi=500):
        fig = plt.gcf()
        fig.set_size_inches(schema['size'][0], schema['size'][1])
        fig.tight_layout()
        fig.savefig(self.filename, dpi=dpi, bbox_inches='tight', filetype=self.filetype)
        plt.close()

    def walk_schema(self, schema, **kwargs):
        """
        dict keyed on row, column with value of parameter x, y
        """

        for i, value in schema['plots'].iteritems():
            for j, items in value.iteritems():
                ax = plt.subplot2grid(schema['grid'], (i-1, j-1))
                self.plot_2d_hist(ax, items[0], items[1],
                                  limits=schema['lim'], logit=kwargs['logit'])

    def plot_2d_hist(self, ax, x, y, cols='b',
                     downsample=None, n_pts=2e4, limits=None,
                     logit=False, **kwargs):
        x_lb = self.FCS.parameters.iloc[:, x-1].loc['Channel_Name']
        y_lb = self.FCS.parameters.iloc[:, y-1].loc['Channel_Name']

        if downsample is None:
            n = n_pts
        else:
            n = int(downsample * self.FCS.data.shape[0])

        if n < self.FCS.data.shape[0]:
            indices = np.random.choice(range(self.FCS.data.shape[0]), int(n),
                                       replace=False)
            dat = self.FCS.data.iloc[indices, :]
            if hasattr(self.FCS, 'cluster') is True:
                cols = self.FCS.cluster[indices]
        else:
            dat = self.FCS.data
            if hasattr(self.FCS, 'cluster') is True:
                cols = self.FCS.cluster

        x_pts = np.ravel(dat[[x-1]].values)
        y_pts = np.ravel(dat[[y-1]].values)
        fsc_pts = np.ravel(dat[[2]].values)

        plt.xlabel(x_lb)
        plt.ylabel(y_lb)
        if limits is None:
            xlims = np.percentile(x_pts, [1, 99]) * np.array([0.8, 1.2])
            ylims = np.percentile(y_pts, [1, 99]) * np.array([0.8, 1.2])
            limits = (min(xlims[0], ylims[0]), max(xlims[1], ylims[1])) * 2

        if self.comp_lines and \
           (x - 1) in self.comp_lines[0].xt_Channel_Number.values:
            legs = []

            # Setup colors
            if hasattr(self.FCS, 'cluster'):
                crange = (min(self.FCS.cluster), max(self.FCS.cluster))
                cn = len(np.unique(self.FCS.cluster))
                cm_name = 'Set1'
            else:
                crange = (0, len(self.comp_lines)-1)
                cn = len(self.comp_lines)
                cm_name = 'YlOrRd'

            cm_sm = mplt.cm.ScalarMappable(norm=mplt.colors.Normalize(vmin=crange[0],
                                                                      vmax=crange[1]),
                                           cmap=cm_name)
            (mplt.colors.Colormap(cm_name, cn))

            # Setup linestyles
            linestyles = np.asarray(['--', '-', '-.', ':'])
            cluster_count = {}

            # Make fit lines
            for i, comp_line_i in enumerate(self.comp_lines):
                (m, m2, b,
                 score, cluster, N) = comp_line_i.loc[comp_line_i.xt_Channel_Number == (x-1),
                                                      ['m', 'm2', 'b', 'score',
                                                       'cluster', 'N']].values[0]
                if cluster is None:
                    cluster = i
                cluster = int(cluster)
                if cluster in cluster_count:
                    cluster_count[cluster] += 1
                else:
                    cluster_count[cluster] = 0

                # Get coords
                i_s = np.random.choice(range(len(y_pts)),
                                       size=min(len(y_pts), 1000),
                                       replace=False)
                ys = y_pts[i_s]
                if m2 is not None:
                    xs = ys * m + fsc_pts[i_s]*m2 + b
                else:
                    xs = ys * m + b
                order = np.argsort(ys)
                ys = ys[order]
                xs = xs[order]

                leg_name = ''.join([str(comp_line_i[xn][0])[0]
                                    for xn in ['model', 'downsample_on_y', 'gate', 'cluster']])

                leg_h, = plt.plot(xs, ys,
                                  c=cm_sm.to_rgba(cluster),
                                  linestyle=linestyles[cluster_count[cluster]],
                                  label='| '.join([leg_name,
                                                   '{:+.3f}'.format(m),
                                                   '{:+.2f}'.format(score),
                                                   '{:.0f}'.format(N)]))
                # for y in np.logspace(limits[0], limits[1], num=nbin * 2):
                #     y_range.append(y)
                #     if m2 is not None:
                #         j = np.mean(fsc_pts[np.where((y_pts >= y - y_bin/2) &
                #                                      (y_pts <= y + y_bin/2))])
                #         x_range.append(y*m + j*m2 + b)
                #     else:
                #         x_range.append(i*m + b)
                # for j in range(len(x_range)-1):
                #     leg_h, = plt.plot(x_range[j:(j+2)],
                #                       y_range[j:(j+2)],
                #                       c=cm_sm.to_rgba(cluster),
                #                       linestyle=linestyles[cluster_count[cluster]],
                #                       label='| '.join([leg_name,
                #                                        '{:+.3f}'.format(m),
                #                                        '{:+.2f}'.format(score),
                #                                        '{:.0f}'.format(N)]))
                legs.append(leg_h)

            plt.legend(handles=legs, fontsize=1.5,
                       bbox_to_anchor=(0.96, 0.04), bbox_transform=ax.transAxes,
                       loc='lower right')
            colors = list(cm_sm.to_rgba(x) for x in cols)
            plt.scatter(x=x_pts, y=y_pts, s=1,
                        marker='.',
                        c=colors,
                        edgecolor='',
                        alpha=0.5)
        else:
            plt.scatter(x=x_pts, y=y_pts, s=1,
                        marker='.',
                        c=cols,
                        edgecolor='',
                        alpha=0.5,
                        cmap=mplt.cm.Set1)  # lw=0

        if self.gate is not None and x_lb in self.gate:
            # NOTE: this is customized only for antibody titer plots
            verts = self.gate[x_lb]
            codes = [mplt.path.Path.MOVETO] + [mplt.path.Path.LINETO] * (len(verts)-2) + \
                    [mplt.path.Path.CLOSEPOLY]
            path = mplt.path.Path(verts, codes)
            patch = mplt.patches.PathPatch(path, facecolor='gray', alpha=0.1, linewidth=0.5)
            ax.add_patch(patch)

        if logit is True:
            if x_lb not in ['FSC-H', 'FSC-A', 'SSC-A']:
                x_pts[np.where(x_pts <= 0)] = 1
                ax.set_xscale('log')
            if y_lb not in ['FSC-H', 'FSC-A', 'SSC-A']:
                y_pts[np.where(y_pts <= 0)] = 1
                ax.set_yscale('log')

        ax.set_xlim(limits[0], limits[1])
        ax.set_ylim(limits[2], limits[3])
        ax.set_yticks([])
        ax.tick_params(axis='both', which='major', labelsize=4)

        if logit is False or (x <= 3 and y <= 3) or (x > 3 and y > 3):
            ax.set_aspect('equal', adjustable='box')
