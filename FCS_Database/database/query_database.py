"""
Class to query database
"""
from os import path
import logging
import pandas as pd

from utils import Vividict

log = logging.getLogger(__name__)


class queryDB(object):
    """
    Constructs query of FCS_Database object
    """

    def __init__(self, fcsdb, **kwargs):
        self.db = fcsdb
        self.session = fcsdb.Session()

        if ('getfiles' in kwargs):
            self.results = self.getfiles(**kwargs)

        self.session.close()

    def getfiles(self, exporttype='dict_dict', **kwargs):
        """
        Collect HP files based on command-line arguments
        ARGUMENTS:
        - exporttype ['dict_dict', 'df'] (requried)
        OUTPUT: dict of dicts (keyed on <case_number><TubeType>)
        """
        TubeCases = self.db.meta.tables['TubeCases']
        TubeTypesInstances = self.db.meta.tables['TubeTypesInstances']
        if 'tubes' in kwargs:
            tubes_to_select = [unicode(x) for x in kwargs['tubes']]
            log.info('Looking for tubes: %s' % tubes_to_select)

            q = self.session.query(TubeCases.c.case_number, TubeCases.c.filename,
                                   TubeCases.c.dirname,
                                   TubeTypesInstances.c.tube_type).\
                filter(TubeTypesInstances.c.tube_type.in_(tubes_to_select))

        if exporttype == 'dict_dict':
            files = Vividict()
            try:
                for x in q.all():
                    files[x.case_number][x.tube_type] = path.join(x.dirname, x.filename)
            except:
                self.session.rollback()
                raise "Failed to query TubeCases"
            return files
        elif exporttype == 'df':
            data = q.first()
            columns = data.keys()
            data = [tuple(data)]
            for row in q.all():
                data.append(row)
            df = pd.DataFrame(data=data, columns=columns)
            df['filepath'] = df.apply(lambda x: path.join(x.dirname, x.filename),
                                      axis=1)
            df.drop(['filename', 'dirname'], axis=1, inplace=True)
            df.sort(['case_number', 'tube_type'], inplace=True)
            return df
        else:
            raise "Unknown type"

