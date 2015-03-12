import re
import pandas as pd
from datetime import datetime

peak_matcher = re.compile('.*peaks.*', re.IGNORECASE)
fn_parser = re.compile("""
        ^\w+
        \s\w+
        \s(\d+)     # month
        \s(\d+)     # day
        \s(\d+)     # year
        \s([\w\s]+) # type
        \.csv\s*$""", re.VERBOSE)
lastdir_parser = re.compile('^\w+\s(\d+)\s(\w+)$')


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

        df = pd.read_csv(fp, header=None).T
        df.columns = df.iloc[0, :]
        df = df.drop(0, axis=0)
        return df

    def __parse_fp(self, fp):
        """ Convert filepath into info """
        fp_comps = fp.split("/")
        lastdir = fp_comps[len(fp_comps)-2]
        fn = fp_comps[len(fp_comps)-1]

        # Dir
        lastdir_m = lastdir_parser.search(lastdir)
        last_dir_year = int(lastdir_m.group(1))
        instr = lastdir_m.group(2)

        # fn
        fn = fn.replace('_', ' ')
        fn = fn.replace('  ', ' ')
        fn_m = fn_parser.search(fn)
        fn_date = datetime.strptime(fn_m.group(1) + fn_m.group(2) + fn_m.group(3), '%m%d%y')
        fn_type = fn_m.group(4)

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
        if fn_type.lower() == '8 peaks':
            bead_type = '8peaks'
        elif fn_type.lower() == 'ultra':
            bead_type = 'ultra'
        else:
            bead_type = fn_type.lower()

        return (fn_date, cyt, bead_type)
