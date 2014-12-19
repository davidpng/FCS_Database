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

        if ('getfiles' in kwargs and kwargs['getfiles'] is True):
            self.results = self.__getfiles(**kwargs)
        elif ('getPmtStats' in kwargs and kwargs['getPmtStats'] is True):
            self.results = self.__getPmtStats(**kwargs)
        elif ('getTubeStats' in kwargs and kwargs['getTubeStats'] is True):
            self.results = self.__getTubeStats(**kwargs)
        elif ('getPmtHistos' in kwargs and kwargs['getPmtHistos'] is True):
            self.results = self.__getPmtHistos(**kwargs)

        self.session.close()

    def __getfiles(self, exporttype='dict_dict', **kwargs):
        """
        Gets files based on specified criteria, organizes by case+tube and returns
        object

        Notable attributes:
        .results -- stores the result of query; datatype specified by <exporttype>

        Keyword arguments:
        exporttype ['dict_dict', 'df'] (default: dict_dict)
        """
        TubeCases = self.db.meta.tables['TubeCases']
        TubeTypesInstances = self.db.meta.tables['TubeTypesInstances']

        # Build query
        self.q = self.session.query(TubeCases.c.case_number, TubeCases.c.filename,
                                    TubeCases.c.dirname,
                                    TubeTypesInstances.c.tube_type).\
            filter(~TubeCases.c.empty)

        self.__add_filters_to_query(**kwargs)

        # Handle export data
        if exporttype == 'dict_dict':
            files = Vividict()
            try:
                for x in self.q.all():
                    files[x.case_number][x.tube_type] = path.join(x.dirname, x.filename)
            except:
                self.session.rollback()
                raise "Failed to query TubeCases"
            return files
        elif exporttype == 'df':
            df = self.__q2df()
            df['filepath'] = df.apply(lambda x: path.join(x.dirname, x.filename),
                                      axis=1)
            df.drop(['filename', 'dirname'], axis=1, inplace=True)
            df.sort(['case_number', 'tube_type'], inplace=True)
            return df
        else:
            raise "Unknown type"

    def __getPmtStats(self, **kwargs):
        """
        Gets PmtStats

        Notable attributes:
        .results -- stores the result of query in dataframe

        """
        PmtStats = self.db.meta.tables['PmtStats']
        TubeCases = self.db.meta.tables['TubeCases']

        # Build query
        self.q = self.session.query(TubeCases.c.cytnum,
                                    TubeCases.c.date,
                                    PmtStats).\
            filter(TubeCases.c.case_tube == PmtStats.c.case_tube).\
            filter(~TubeCases.c.empty).\
            order_by(TubeCases.c.date)

        self.__add_filters_to_query(**kwargs)

        df = self.__q2df()
        return df

    def __getTubeStats(self, **kwargs):
        """
        Gets TubeStats

        Notable attributes:
        .results -- stores the result of query in dataframe

        """
        TubeStats = self.db.meta.tables['TubeStats']
        TubeCases = self.db.meta.tables['TubeCases']

        # Build query
        self.q = self.session.query(TubeCases.c.cytnum,
                                    TubeCases.c.date,
                                    TubeStats).\
            filter(TubeStats.c.case_tube == TubeCases.c.case_tube).\
            filter(~TubeCases.c.empty).\
            order_by(TubeCases.c.date)

        self.__add_filters_to_query(**kwargs)

        df = self.__q2df()
        return df

    def __getPmtHistos(self, **kwargs):
        """
        Gets Pmt Histos

        Notable attributes:
        .results -- stores the result of query in dataframe

        """
        PmtHistos = self.db.meta.tables['PmtHistos']
        TubeCases = self.db.meta.tables['TubeCases']

        # Build query
        self.q = self.session.query(TubeCases.c.cytnum,
                                    TubeCases.c.date,
                                    PmtHistos).\
            filter(PmtHistos.c.case_tube == TubeCases.c.case_tube).\
            filter(~TubeCases.c.empty).\
            order_by(TubeCases.c.date,
                     PmtHistos.c.case_tube, PmtHistos.c["Channel Name"], PmtHistos.c.bin)

        self.__add_filters_to_query(**kwargs)

        df = self.__q2df()
        return df

    def __add_filters_to_query(self, **kwargs):
        """ Add filters specified in kwargs to self.q

        Keyword arguments:
        tubes -- <list> Select set based on tube types
        daterange -- <list> [X,X] Select set based on date between daterange
        """

        TubeTypesInstances = self.db.meta.tables['TubeTypesInstances']
        TubeCases = self.db.meta.tables['TubeCases']

        if 'tubes' in kwargs:
            tubes_to_select = [unicode(x) for x in kwargs['tubes']]
            log.info('Looking for tubes: %s' % tubes_to_select)
            self.q = self.q.filter(TubeTypesInstances.c.tube_type.in_(tubes_to_select))

        if 'daterange' in kwargs and kwargs['daterange'] is not None:
            date_start = datetime.strptime(kwargs['daterange'][0], '%Y-%m-%d')
            date_end = datetime.strptime(kwargs['daterange'][1], '%Y-%m-%d')
            self.q = self.q.filter(func.date(TubeCases.c.date).between(date_start, date_end))

    def __q2df(self):
        """ Convert a query object to a pandas dataframe """

        data = self.q.first()

        if data is not None:
            columns = data.keys()
            data = [tuple(data)]
            for row in self.q.all():
                data.append(row)
            df = pd.DataFrame(data=data, columns=columns)
            df.drop_duplicates(inplace=True)
            return df
        else:
            return {}
