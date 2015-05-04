import re
import pandas as pd
import numpy as np
from datetime import datetime

from FlowAnal.FCS_subroutines.loadFCS import parse_channel_name

peak_matcher = re.compile('.*peaks.*', re.IGNORECASE)
fn_parser = re.compile("""
        ^\w*
        (\s\w+)
        \s(\d+)     # month
        \s(\d+)     # day
        \s(\d+)     # year
        \s([\w]+) # type
        \.csv\s*$""", re.VERBOSE)

lastdir_parser = re.compile('^\w+?\s?(\d+)\s(\w+)$')
lastdir_parser2 = re.compile('^(\w+)\s?(\w*\s)?(\d+)$')


def pop2fluo(x):
    y = x.split('-')
    if len(y) == 2:
        return y[0]
    else:
        return '-'.join(y[0:(len(y)-1)])


class load_beadQC_from_csv(object):
    def __init__(self, fp):

        # Parse fp
        (self.date, self.cyt, self.bead_type) = self.__parse_fp(fp)

        # Load data
        if self.bead_type == '8peaks':
            self.df = self.__load_8peaks(fp)
            self.df['cyt'] = self.cyt
            self.df['date'] = self.date
        elif self.bead_type == 'ultra':
            self.df = self.__load_ultra(fp)
            self.df['cyt'] = self.cyt
            self.df['date'] = self.date

    def __load_ultra(self, fp):
        """ Read fp file for ultra beads and turn into df """

        data = pd.read_csv(fp)
        if data.shape[1] > 3:
            data = data.iloc[:, 0:3]

        if data.Populations[1] != 'Populations':
            data = data.drop(data.index[1])
            data.reset_index(inplace=True, drop=True)

        headers = data.iloc[range(1, data.shape[0], 2), :]
        data = data.iloc[range(0, data.shape[0], 2), :]
        tests = ['Mean' in x for x in headers.values[:, 1]] + \
                ['CV' in x for x in headers.values[:, 2]]
        if tests.count(False) != 0:
            print headers
            raise ValueError('Mean or CV header wrong')
        data.columns = ['Fluorophore', 'Mean', 'CV']
        data.reset_index(inplace=True, drop=True)
        tmp = data.Fluorophore.apply(parse_channel_name)
        data.Fluorophore = zip(*tmp)[0]
        data.dropna(inplace=True)

        return data

    def __load_8peaks(self, fp):
        """ Read fp file and turn into dataframe """

        try:
            df = pd.read_csv(fp, header=None).T
        except pd.parser.CParserError:
            try:
                df = pd.read_csv(fp, header=None, skiprows=4).T  # Skip some lines
            except pd.parser.CParserError:
                df = pd.read_csv(fp, header=None, skiprows=6).T  # Skip some lines

        df.columns = df.iloc[0, :]
        df = df.drop(0, axis=0)
        df.drop_duplicates(inplace=True)

        if (df.shape[0] not in (9, 10, 11, 12)) or \
           (df.shape[1] not in (8, 9, 10, 11)):
            print df
            raise ValueError('FP {} made df of shape {}'.format(fp,
                                                                df.shape))

        df.Populations = df.Populations.str.replace(' Mean', '')
        tmp = df.Populations.apply(parse_channel_name)
        df.Populations = zip(*tmp)[2]

        return df

    def __parse_fp(self, fp):
        """ Convert filepath into info """
        fp_comps = fp.split("/")
        lastdir = fp_comps[len(fp_comps)-2]
        fn = fp_comps[len(fp_comps)-1]

        # Dir
        try:
            lastdir_m = lastdir_parser.search(lastdir)
            last_dir_year = int(lastdir_m.group(1))
            instr = lastdir_m.group(2)
        except AttributeError:
            lastdir_m = lastdir_parser2.search(lastdir)
            last_dir_year = int(lastdir_m.group(3))
            instr = lastdir_m.group(1)

        # fn
        fn = re.sub('(\d)_(\d)', '\1 \2', fn)
        fn = fn.replace('  ', ' ')
        fn = fn.replace('8 peak', '8peak')
        fn_m = fn_parser.search(fn)

        try:
            fn_date = datetime.strptime(fn_m.group(2) + fn_m.group(3) + fn_m.group(4), '%m%d%y')
        except:
            try:
                fn_date = datetime.strptime(fn_m.group(2) + fn_m.group(3) + fn_m.group(4),
                                            '%m%d%Y')
            except:
                raise AttributeError('FN {} datetime not extractable!!'.format(fn))

        fn_type = fn_m.group(5)

        # Date check
        if last_dir_year != fn_date.year:
            raise ValueError('Years do not match')

        # Parse cyt
        if instr.upper() == 'A':
            cyt = '1'
        elif instr.upper() == 'B':
            cyt = '2'
        elif instr.upper() == 'C':
            cyt = '3'
        else:
            cyt = instr.upper()

        # Parse bead_type
        if '8peak' in fn_type.lower():
            bead_type = '8peaks'
        elif 'ultra' in fn_type.lower():
            bead_type = 'ultra'
        else:
            bead_type = fn_type.lower()

        return (fn_date, cyt, bead_type)
