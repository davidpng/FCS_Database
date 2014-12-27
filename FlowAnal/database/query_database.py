"""
Class to query database
"""
from os import path
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased, lazyload

from FlowAnal.utils import Vividict
from FlowAnal.database.FCS_declarative import *

from sqlalchemy.dialects import sqlite

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
        elif ('getPmtCompCorr' in kwargs and kwargs['getPmtCompCorr'] is True):
            self.results = self.__getPmtCompCorr(**kwargs)

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
        log.info('Looking for files')
        # Build query
        self.q = self.session.query(TubeCases.case_number, TubeCases.filename,
                                    TubeCases.dirname,
                                    TubeTypesInstances.tube_type,
                                    TubeCases.date).\
            join(TubeTypesInstances).\
            filter(~TubeCases.empty)

        # keep track of explicitly joined tables
        self.q.joined_tables = ['TubeCases', 'TubeTypesInstances']

        # Add common filters
        self.__add_filters_to_query(**kwargs)

        log.debug('Query:')
        log.debug(self.q.statement)

        # Handle export data
        if exporttype == 'dict_dict':
            files = Vividict()
            try:
                for x in self.q.all():
                    files[x.case_number][x.tube_type][x.date] = path.join(x.dirname, x.filename)
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
        log.info('Looking for PmtStats')

        # Build query
        self.q = self.session.query(TubeCases.cytnum,
                                    TubeCases.date,
                                    TubeStats.total_events,
                                    PmtStats).\
            join(PmtTubeCases, PmtStats.Pmt).\
            join(TubeCases, PmtTubeCases.Tube).\
            join(TubeStats, TubeCases.Stats).\
            filter(~TubeCases.empty).\
            order_by(TubeCases.date)

        # keep track of explicitly joined tables
        self.q.joined_tables = ['TubeCases', 'PmtTubeCases', 'PmtStats', 'TubeStats']

        self.__add_filters_to_query(**kwargs)
        df = self.__q2df()

        return df

    def __getTubeStats(self, **kwargs):
        """
        Gets TubeStats

        Notable attributes:
        .results -- stores the result of query in dataframe

        """
        log.info('Looking for TubeStats')

        # Build query
        self.q = self.session.query(TubeCases.cytnum,
                                    TubeCases.date,
                                    TubeStats).\
            join(TubeStats).\
            filter(~TubeCases.empty).\
            order_by(TubeCases.date)

        # keep track of explicitly joined tables
        self.q.joined_tables = ['TubeCases', 'TubeStats']

        self.__add_filters_to_query(**kwargs)

        df = self.__q2df()

        return df

    def __getPmtHistos(self, **kwargs):
        """
        Gets Pmt Histos

        Notable attributes:
        .results -- stores the result of query in dataframe

        """
        log.info('Looking for PmtHistos')
        # Build query
        self.q = self.session.query(TubeCases.cytnum,
                                    TubeCases.date,
                                    PmtHistos).\
            join(PmtTubeCases, PmtHistos.Pmt).\
            join(TubeCases, PmtTubeCases.Tube).\
            filter(~TubeCases.empty).\
            order_by(TubeCases.date,
                     PmtHistos.case_tube_idx,
                     PmtHistos.Channel_Number,
                     PmtHistos.bin)
        self.q.joined_tables = ['TubeCases', 'PmtHistos', 'PmtTubeCases']
        self.__add_filters_to_query(**kwargs)

        df = self.__q2df()
        return df

    def __getPmtCompCorr(self, **kwargs):
        """
        Gets Pmt Compensation Correlation

        Notable attributes:
        .results -- stores the result of query in dataframe

        """
        log.info('Looking for PmtCompCorr')
        PmtTubeCasesFROM = aliased(PmtTubeCases)
        PmtTubeCasesIN = aliased(PmtTubeCases)

        # Build query
#         q_text = """SELECT TubeCases.cytnum,
# TubeCases.date,
# PmtTubeCasesIN.Antigen as Antigen_IN,
# PmtTubeCasesIN.Fluorophore as Fluorophore_IN,
# PmtTubeCasesFROM.Antigen as Antigen_FROM,
# PmtTubeCasesFROM.Fluorophore as Fluorophore_FROM,
# PmtCompCorr.*
# FROM PmtCompCorr
# INNER JOIN TubeCases USING (case_tube_idx)
# INNER JOIN PmtTubeCases AS PmtTubeCasesIN ON (PmtTubeCasesIN.case_tube_idx = PmtCompCorr.case_tube_idx
# AND PmtTubeCasesIN."Channel_Number" = PmtCompCorr."Channel_Number IN")
# INNER JOIN PmtTubeCases AS PmtTubeCasesFROM ON (PmtTubeCasesFROM.case_tube_idx = PmtCompCorr.case_tube_idx
# AND PmtTubeCasesFROM."Channel_Number" = PmtCompCorr."Channel_Number FROM")
# WHERE TubeCases.empty = 0
# ORDER BY TubeCases.date, PmtCompCorr.case_tube_idx, PmtCompCorr."Channel_Number IN"
# """
        # self.q = self.session.query("cytnum", "date",
        #                             "Antigen_IN", "Fluorophore_IN",
        #                             "Antigen_FROM", "Fluorophore_FROM",
        #                             PmtCompCorr).\
        #     from_statement(text(q_text))

        self.q = self.session.query(TubeCases.date.label('date'),
                                    TubeCases.cytnum.label('cytnum'),
                                    PmtTubeCasesIN.Antigen.label('Antigen_IN'),
                                    PmtTubeCasesIN.Fluorophore.label('Fluorophore_IN'),
                                    PmtTubeCasesFROM.Antigen.label('Antigen_FROM'),
                                    PmtTubeCasesFROM.Fluorophore.label('Fluorophore_FROM'),
                                    PmtCompCorr).\
            join(PmtTubeCasesFROM, PmtCompCorr.PMT_FROM).\
            join(PmtTubeCasesIN, PmtCompCorr.PMT_IN).\
            join(TubeCases, PmtTubeCasesIN.Tube)

        self.q.joined_tables = ['TubeCases', 'PmtTubeCasesFROM', 'PmtTubeCasesIN', 'PmtCompCorr']

        self.__add_filters_to_query(**kwargs)

        df = self.__q2df()
        return df

    def __add_filters_to_query(self, **kwargs):
        """ Add filters specified in kwargs to self.q

        Keyword arguments:
        tubes -- <list> Select set based on tube types
        daterange -- <list> [X,X] Select set based on date between daterange
        """

        if 'tubes' in kwargs and kwargs['tubes'] is not None:
            tubes_to_select = [unicode(x) for x in kwargs['tubes']]
            log.info('Looking for tubes: %s' % tubes_to_select)
            self.q = self.q.filter(TubeTypesInstances.tube_type.in_(tubes_to_select))
            if 'TubeTypesInstances' not in self.q.joined_tables:
                self.q = self.q.join(TubeTypesInstances)

        if 'daterange' in kwargs and kwargs['daterange'] is not None:
            log.info('Looking for daterange: [%s, %s]' % (kwargs['daterange'][0],
                                                          kwargs['daterange'][1]))
            date_start = datetime.strptime(kwargs['daterange'][0], '%Y-%m-%d')
            date_end = datetime.strptime(kwargs['daterange'][1], '%Y-%m-%d')
            self.q = self.q.filter(func.date(TubeCases.date).between(date_start, date_end))
            if 'TubeCases' not in self.q.joined_tables:
                self.q = self.q.join(TubeCases)

        if 'cases' in kwargs and kwargs['cases'] is not None:
            cases_to_select = [unicode(x) for x in kwargs['cases']]
            log.info('Looking for cases #%s' % ", ".join(cases_to_select))
            self.q = self.q.filter(TubeCases.case_number.in_(cases_to_select))
            if 'TubeCases' not in self.q.joined_tables:
                self.q = self.q.join(TubeCases)

    def compile_query(self):
        statement = self.q.statement.compile(dialect=sqlite.dialect())
        return statement, statement.params

    def __q2df(self):
        """ Convert a query object to a pandas dataframe """

        qstring, params = self.compile_query()
        df = pd.read_sql_query(sql=qstring,
                               con=self.db.engine,
                               params=params)
        return df

        # data = pd.DataFrame(self.q.all())
        # data.columns = self.q.first().keys()
        # return data

        # data = self.q.first()
        # if data is not None:
        #     columns = data.keys()
        #     data = [tuple(data)]
        #     for row in self.q.all():
        #         data.append(row)
        #     df = pd.DataFrame(data=data, columns=columns)
        #     df.drop_duplicates(inplace=True)
        #     print df
        #     return df
        # else:
        #     return {}
