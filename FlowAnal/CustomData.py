import logging
import pandas as pd

log = logging.getLogger(__name__)


class CustomData(object):
    """
    This class I/O's custom case data

    INPUT: tab-delimited text

    ATTRIBUTES:
    .dat -- pd DataFrame from input text. row index = 'case_number'
    """
    def __init__(self, fp, sep="\t"):
        self.dat = self.__load(fp, sep=sep)

    def __load(self, filepath, sep):

        a = pd.read_csv(filepath, sep=sep)

        # ### Handle column names ###
        a.columns = [c.lower() for c in a.columns.values]
        a_cols = a.columns.tolist()

        # Convert 'CASE*' => 'case_number'
        case_index = next((index for index, value in enumerate(a_cols)
                           if value[:4] == 'case'), None)
        if case_index is not None:
            a_cols[case_index] = 'case_number'

        a.columns = a_cols

        a.set_index(keys='case_number', drop=True, inplace=True)

        # Remove two letters if present from all
        cases = a.index.tolist()
        if cases[0][0:2].startswith('HP'):
            cases = [x[2:] for x in cases]
            a.index = cases

        return a

