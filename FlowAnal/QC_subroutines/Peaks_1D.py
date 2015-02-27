import numpy as np
import pandas as pd
from scipy.signal import find_peaks_cwt, argrelmax
from sklearn.grid_search import GridSearchCV
from sklearn.neighbors import KernelDensity
import itertools

from matplotlib import pyplot as plt
from ggplot import *
import logging
log = logging.getLogger(__name__)


class Peaks_1D(object):
    """ Class that encapsulates methods for subdividing 1D vectors of intensity data """
    def __init__(self, data, name, case_tube_idx=None):
        self.dat = data
        self.name = name
        self.case_tube_idx = case_tube_idx

    def find_peaks_cwt(self):
        """ Identify peaks using scipy.signal.find_peaks_cwt """

        peaks = find_peaks_cwt(vector=self.dat,
                               widths=np.arange(1, 10),
                               min_snr=1)
        self.peaks = list(peaks)
        log.debug("{} <=> {}".format(self.peaks, self.dat[self.peaks]))

    def local_max(self, max_peaks=5, min_score=0.1, **kwargs):
        """ Identify peaks using scipy.signal.argrelmax """

        peaks = argrelmax(self.dat, order=2)
        self.peaks = list(peaks[0])

        log.debug("Found peaks {} <=> {}".format(self.peaks, self.dat[self.peaks]))

        # Calc scores
        self.peak_scores = []
        for i, p in enumerate(self.peaks):
            score = self.calc_peak_score(p)
            self.peak_scores.append(score)

        # Exclude for score under min_score
        if min_score is not None and min_score != 0:
            p_i = np.asarray(self.peak_scores)
            p_i = np.where(p_i < min_score)[0]
            log.debug("Removing peaks {} because under threshold".format(p_i))
            i = 0
            while i < len(p_i):
                self.peaks.pop(p_i[i])
                self.peak_scores.pop(p_i[i])
                p_i -= 1
                i += 1

        # Trim peaks
        trimmed_peaks = self.trim_peaks(self.peaks, inplace=False, **kwargs)
        if len(trimmed_peaks) != len(self.peaks):
            excluded_peaks = [x for x in self.peaks
                              if x not in trimmed_peaks]
            log.debug('Excluding {}'.format(excluded_peaks))
            for x in excluded_peaks:
                ix = self.peaks.index(x)
                self.peaks.pop(ix)
                self.peak_scores.pop(ix)
            for x in trimmed_peaks:
                added = False
                if x not in self.peaks:
                    score = self.calc_peak_score(x)
                    self.peaks.append(x)
                    self.peak_scores.append(score)
                    added = True

                if added is True:
                    self.peak_scores = [x for (y, x) in sorted(zip(self.peaks,
                                                                   self.peak_scores),
                                                               key=lambda pair: pair[0])]
                    self.peaks = sorted(self.peaks)

        log.debug("Trimmed to peaks {} <=> {}".format(self.peaks, self.dat[self.peaks]))

        # Pick a max of max_peaks
        if len(self.peaks) > max_peaks:
            p_i = np.asarray(self.peak_scores)
            p_i = np.argsort(p_i)[::-1]
            p_i = p_i[range(max_peaks)]
            p_i = np.sort(p_i)
            self.peaks = [self.peaks[i] for i in p_i]
            self.peak_scores = [self.peak_scores[i] for i in p_i]

        log.debug("Top {} peaks {} <=> {}".format(max_peaks,
                                                  self.peaks, self.dat[self.peaks]))

    def calc_peak_score(self, p):
        """ Calculate peak score and return """

        score = self.dat[p]*6
        subs = np.array([p-4, p-3, p - 2, p + 2, p+3, p+4])
        subs = subs[(subs >= 0) & (subs < len(self.dat))]
        score -= sum(self.dat[subs]) * 6/len(subs)
        return score

    def trim_peaks(self, peaks=None, pdist=5, inplace=True):
        """ Pick highest peak if there are several within distance pdist """

        if peaks is None:
            peaks = self.peaks
        peaks.sort()
        final_peaks = []

        i = 0
        while i <= len(peaks)-1:

            # Make peak grouping
            peak_group = [peaks[i]]
            for j in range(i+1, len(peaks)):
                if peaks[j] <= peaks[i] + pdist:
                    peak_group.append(peaks[j])
                    i += 1
                else:
                    break

            # Pick peak
            if len(peak_group) > 1:
                peak_avg = np.average(peak_group,
                                      weights=[self.dat[p]
                                               for p in peak_group])
                final_peaks.append(int(peak_avg))
            else:
                final_peaks = final_peaks + peak_group

            i += 1

        if inplace is True:
            self.peaks = final_peaks
            log.debug(self.peaks)
        else:
            return final_peaks

    def plot(self):
        """ Print data with peaks labeled """

        plt.figure(figsize=(10, 6))
        plt.plot(range(len(self.dat)), self.dat)
        if hasattr(self, 'peaks'):
            plt.plot(self.peaks, self.dat[self.peaks], 'ro')
            for i, x in enumerate(self.peaks):
                plt.annotate('{:.2f}'.format(self.peak_scores[i]), (x, self.dat[x]))

        plt.title(self.name + ' peaks')
        plt.savefig(self.name + '.png', bbox_inches='tight', dpi=100)
        plt.close()


class Peaks_1D_Set(object):
    """ Set of Peaks_1D objects """
    def __init__(self, name):
        self.dat = []
        self.peaks_all = []
        self.name = name

    def append(self, peaks):
        """ Add new Peak_1D to set """
        self.dat.append(peaks)
        self.peaks_all += peaks.peaks

    def find_peaks(self):
        """ Find peaks from all peak data """
        all_peaks = np.asarray(self.peaks_all)
        x_grid = np.linspace(0, 100, 100)
        grid = GridSearchCV(KernelDensity(),
                            {'bandwidth': np.linspace(1.0, 10.0, 20)},
                            cv=20)
        grid.fit(all_peaks[:, None])
        kde = grid.best_estimator_
        pdf = np.exp(kde.score_samples(x_grid[:, None]))
        group_peaks = Peaks_1D(pdf)
        group_peaks.local_max()

        self.group_peaks = group_peaks

    def n_group_peaks(self, thresh=1.0, percentile=85):
        """ Pick how many group peaks to align """

        counts = []
        for x in self.dat:
            n = 0
            for i, peak in enumerate(x.peaks):
                if x.peak_scores[i] >= thresh:
                    n += 1
            counts.append(n)

        choice = np.percentile(counts, percentile)
        self.n_peaks = choice.astype(int)

    def label_peaks(self, thresh=1.0):
        """ Assign labels to peaks for each sample

        - This requires n_group_peaks to have runA
        """

        peak_names = ['P{}'.format(x) for x in range(self.n_peaks)]

        # Initialize peak locations (Using specimens with exactly self.n_peaks peaks above <thresh>
        d = []
        for x in self.dat:
            gpeaks = [p for i, p in enumerate(x.peaks)
                      if x.peak_scores[i] >= thresh]
            if len(gpeaks) == self.n_peaks:
                d.append([x.case_tube_idx] + gpeaks)

        df = pd.DataFrame(d, columns=['case_tube_idx'] + peak_names)
        df.set_index(['case_tube_idx'], drop=True, inplace=True)
        medpeaks = df.median().values

        # Label peaks
        for x in self.dat:
            peaks = [None for i in range(len(medpeaks))]
            log.info("Peaks: {}, medians: {}".format(x.peaks, medpeaks))

            # Align peaks
            #  TODO: if len(x.peaks) <= len(medpeaks)...
            #  allow selection of range(1, len(x.peaks)) peaks
            if len(x.peaks) == len(medpeaks):
                peaks = x.peaks
            elif len(x.peaks) < len(medpeaks):
                pdist = float("inf")
                mp_ixs = None
                iter = itertools.combinations(range(len(medpeaks)), len(x.peaks))
                for ixs in iter:
                    mp_i = [medpeaks[i] for i in ixs]
                    pdist_i = sum(abs(np.subtract(mp_i, x.peaks)))
                    if pdist_i < pdist:
                        pdist = pdist_i
                        mp_ixs = ixs
#                print "MP_ixs: {}".format(mp_ixs)
                j = 0
                for i in range(len(medpeaks)):
                    if i in mp_ixs:
                        peaks[i] = x.peaks[j]
                        j += 1
                        if j == len(x.peaks):
                            break
            else:  # len(medpeaks) < len(x.peaks)
                pdist = float("inf")
                pks = None
                for pks_i in itertools.combinations(x.peaks, len(medpeaks)):
                    pdist_i = sum(abs(np.subtract(pks_i, medpeaks)))
                    if pdist_i < pdist:
                        pdist = pdist_i
                        pks = pks_i
                peaks = pks

#            print "Initial {} => final {}".format(x.peaks, peaks)
            # Add to df
            if x.case_tube_idx in df.index:
                df.loc[x.case_tube_idx, :] = peaks
            else:
                tmp = pd.DataFrame([tuple(peaks)], columns=peak_names, index=[x.case_tube_idx])
                df = df.append(tmp)
            df.index.names = ['case_tube_idx']

            # Recalculate medians
            medpeaks = df.median().values

        return df

