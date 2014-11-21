"""
Class to query database
"""
from os import path
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy.sql import func

from FlowAnal.utils import Vividict

log = logging.getLogger(__name__)


class queryDB(object):
    """
    Object interface to construct queries of FCS_Database objects (sqlite db) \
    and return object

    Notable attributes:
    .results -- stores the result of query; datatype specified by <exporttype>

    Keyword Arguments:
    fcsdb -- loaded FCS_database object (sqlite db)
    getfiles -- Use getfiles()
    exporttype -- ['dict_dict', 'df'] set return filetype (default: 'dict_dict')
    tubes -- <list> Select set based on tube types
    daterange -- <list> [X,X] Select set based on date between daterange

    """

    def __init__(self, fcsdb, **kwargs):
        self.db = fcsdb
        self.session = fcsdb.Session()

        if ('getfiles' in kwargs):
            self.results = self.__getfiles(**kwargs)

        self.session.close()

    def __getfiles(self, exporttype='dict_dict', **kwargs):
        """
        Gets files based on specified criteria, organizes by case+tube and returns
        object

        Notable attributes:
        .results -- stores the result of query; datatype specified by <exporttype>

        Keyword arguments:
        exporttype ['dict_dict', 'df'] (default: dict_dict)
        tubes -- <list> Select set based on tube types
        daterange -- <list> [X,X] Select set based on date between daterange

        """
        TubeCases = self.db.meta.tables['TubeCases']
        TubeTypesInstances = self.db.meta.tables['TubeTypesInstances']

        # Handle query
        if 'tubes' in kwargs:
            tubes_to_select = [unicode(x) for x in kwargs['tubes']]
            log.info('Looking for tubes: %s' % tubes_to_select)
            if 'daterange' in kwargs and kwargs['daterange'] is not None:
                date_start = datetime.strptime(kwargs['daterange'][0], '%Y-%m-%d')
                date_end = datetime.strptime(kwargs['daterange'][1], '%Y-%m-%d')
                q = self.session.query(TubeCases.c.case_number, TubeCases.c.filename,
                                       TubeCases.c.dirname,
                                       TubeTypesInstances.c.tube_type).\
                    filter(TubeTypesInstances.c.tube_type.in_(tubes_to_select)).\
                    filter(~TubeCases.c.empty).\
                    filter(func.date(TubeCases.c.date).between(date_start, date_end))
            else:
                q = self.session.query(TubeCases.c.case_number, TubeCases.c.filename,
                                       TubeCases.c.dirname,
                                       TubeTypesInstances.c.tube_type).\
                    filter(TubeTypesInstances.c.tube_type.in_(tubes_to_select)).\
                    filter(~TubeCases.c.empty)

        # Handle export data
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
            df.drop_duplicates(inplace=True)
            df['filepath'] = df.apply(lambda x: path.join(x.dirname, x.filename),
                                      axis=1)
            df.drop(['filename', 'dirname'], axis=1, inplace=True)
            df.sort(['case_number', 'tube_type'], inplace=True)
            return df
        else:
            raise "Unknown type"

