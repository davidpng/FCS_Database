import re
import pandas as pd
from datetime import datetime

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


class load_beadQC_from_csv(object):
    def __init__(self, fp):

        # Parse fp
        (self.date, self.cyt, self.bead_type) = self.__parse_fp(fp)

        # Load data
        if self.bead_type == '8peaks':
            self.df = self.__load_8peaks(fp)
            self.df['cyt'] = self.cyt
            self.df['date'] = self.date

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

        if (df.shape[0] not in (9, 10, 11, 12)) or \
           (df.shape[1] not in (9, 10, 11)):
            print df
            raise ValueError('FP {} made df of shape {}'.format(fp,
                                                                df.shape))
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
                raise AttributeError('FN {} not working!!'.format(fn))

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
