"""
Class to query database
"""
from os import path
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy import and_
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased
from sqlalchemy.dialects import sqlite

from FlowAnal.utils import Vividict
from FlowAnal.database.FCS_declarative import *

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
        log.info('Querying...')

        # If not specified, default to not_flagged to True
        if 'not_flagged' not in kwargs.keys():
            kwargs['not_flagged'] = True

        # Choose query message based on kwargs
        qmethods = ['getfiles', 'getPmtStats', 'getTubeStats',
                    'getPmtCompCorr', 'getPmtHistos', 'getTubeInfo',
                    'getCreationDate', 'getCases', 'pick_cti']
        qmethod = [m for m in qmethods
                   if (m in kwargs.keys() and kwargs[m] is True)]

        dmethods = ['delCasesByCustom', 'delCases', 'delTubeCases',
                    'updateProblemTubeCases']
        dmethod = [m for m in dmethods
                   if (m in kwargs.keys() and kwargs[m] is True)]

        if len(qmethod) > 1:
            print 'Multiple query methods specified: %s by kwargs: %s' % (qmethod,
                                                                          kwargs)
        elif len(qmethod) == 1:
            self.results = getattr(self, '_queryDB__' + qmethod[0])(**kwargs)
        elif len(dmethod) == 1:
            getattr(self, '_queryDB__' + dmethod[0])(**kwargs)
        else:
            raise ValueError('query not specified properly: %s' %
                             '='.join(key, value) for key, value in kwargs.items())

        self.session.close()

    def __getTubeInfo(self, exporttype='dict_dict', **kwargs):
        """
        Gets files based on specified criteria, organizes by case, tube_type, and date and returns
        object (either dataframe or dict of dict

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
                                    TubeCases.date,
                                    TubeCases.flag).\
            join(TubeTypesInstances)

        # keep track of explicitly joined tables
        self.q.joined_tables = ['TubeCases', 'TubeTypesInstances']

        # Add common filters
        self.__add_mods_to_query(**kwargs)

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
                raise Exception("Failed to query TubeCases")
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

    def __getfiles(self, exporttype='dict_dict', **kwargs):
        """
        Gets files based on specified criteria, organizes by case, case_tube_idx and returns
        object (either dataframe or dict of dict

        Notable attributes:
        .results -- stores the result of query; datatype specified by <exporttype>

        Keyword arguments:
        exporttype ['dict_dict', 'df'] (default: dict_dict)
        """
        log.info('Looking for files')
        # Build query
        self.q = self.session.query(TubeCases.case_number,
                                    TubeCases.case_tube_idx,
                                    TubeCases.filename,
                                    TubeCases.dirname)

        # keep track of explicitly joined tables
        self.q.joined_tables = ['TubeCases']

        # Add common filters
        self.__add_mods_to_query(**kwargs)

        log.debug('Query:')
        log.debug(self.q.statement)

        # Handle export data
        if exporttype == 'dict_dict':
            files = Vividict()
            try:
                for x in self.q.all():
                    files[x.case_number][x.case_tube_idx] = path.join(x.dirname, x.filename)
            except:
                self.session.rollback()
                raise "Failed to query TubeCases"
            return files
        elif exporttype == 'df':
            df = self.__q2df()
            df['filepath'] = df.apply(lambda x: path.join(x.dirname, x.filename),
                                      axis=1)
            df.drop(['filename', 'dirname'], axis=1, inplace=True)
            df.sort(['case_number', 'case_tube_idx'], inplace=True)
            return df
        else:
            raise "Unknown type"

    def __pick_cti(self, **kwargs):
        """
        Picks a single case_tube_idx for each case,
        filters on specified criteria, and returns pd.DataFrame of case, case_tube_idx

        Notable attributes:
        .results -- stores the result of query; datatype specified by <exporttype>
        """
        log.info('Looking for case_tube_indx\'s')

        # Build query
        # ## First case_tube_idx
        q1 = self.session.query(TubeCases.case_number,
                                func.max(func.datetime(TubeCases.date)).label("last_dttm")).\
            group_by(TubeCases.case_number)
        q1.joined_tables = ['TubeCases']
        q1 = add_mods_to_query(q1, **kwargs)
        q1 = q1.subquery()

        self.q = self.session.query(TubeCases.case_number,
                                    func.max(TubeCases.case_tube_idx).label("case_tube_idx")).\
            join(q1, and_(TubeCases.case_number == q1.c.case_number,
                          TubeCases.date == q1.c.last_dttm)).\
            group_by(TubeCases.case_number)
        self.q.joined_tables = ['TubeCases']

        # Add common filters
        self.__add_mods_to_query(**kwargs)
        log.debug("\nQuery:\n{}\n".format(self.q.statement))

        # Output
        df = self.__q2df()
        df.sort(['case_number', 'case_tube_idx'], inplace=True)
        return df

    def __getCases(self, aslist=False, **kwargs):
        """ Return list of cases """
        self.q = self.session.query(Cases.case_number)
        self.q.joined_tables = ['Cases']
        self.__add_mods_to_query(**kwargs)
        d = self.q.all()

        if aslist is False:
            return d
        else:
            return [c.case_number for c in d]

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
                                    PmtTubeCases.Antigen,
                                    PmtTubeCases.Fluorophore,
                                    PmtTubeCases.Channel_Name,
                                    PmtTubeCases.Voltage,
                                    TubeTypesInstances.tube_type,
                                    PmtStats).\
            join(PmtTubeCases, PmtStats.Pmt).\
            join(TubeCases, PmtTubeCases.Tube).\
            join(TubeStats, TubeCases.Stats).\
            join(TubeTypesInstances, TubeCases.TubeTypesInstance).\
            order_by(func.datetime(TubeCases.date))

        # keep track of explicitly joined tables
        self.q.joined_tables = ['TubeCases', 'PmtTubeCases', 'PmtStats',
                                'TubeStats', 'TubeTypesInstances']

        self.__add_mods_to_query(**kwargs)
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
                                    TubeCases.case_number,
                                    TubeTypesInstances.tube_type,
                                    TubeStats).\
            join(TubeCases, TubeStats.Tube).\
            join(TubeTypesInstances, TubeCases.TubeTypesInstance).\
            order_by(func.datetime(TubeCases.date))

        # keep track of explicitly joined tables
        self.q.joined_tables = ['TubeCases', 'TubeStats',
                                'TubeTypesInstances']

        self.__add_mods_to_query(**kwargs)

        df = self.__q2df()
        return df

    def __getCaseAnnotations(self, **kwargs):
        """
        Gets Case-level annotations

        Notable attributes:
        .results -- stores the result of query in dataframe
        """
        log.info('Looking for Case annotations')

        # Build query
        self.q = self.session.query(TubeCases.case_tube_idx,
                                    TubeCases.date,
                                    TubeCases.date,
                                    TubeCases.num_events,
                                    TubeCases.cytnum,
                                    CustomCaseData).\
            join(Cases, TubeCases.Case).\
            join(CustomCaseData, Cases.CustomData).\
            order_by(TubeCases.case_tube_idx)

        # keep track of explicitly joined tables
        self.q.joined_tables = ['TubeCases', 'Cases',
                                'CustomCaseData']

        self.__add_mods_to_query(**kwargs)

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
                                    PmtTubeCases.Antigen,
                                    PmtTubeCases.Fluorophore,
                                    PmtHistos).\
            join(PmtTubeCases, PmtHistos.Pmt).\
            join(TubeCases, PmtTubeCases.Tube).\
            order_by(TubeCases.date,
                     PmtHistos.case_tube_idx,
                     PmtHistos.Channel_Number,
                     PmtHistos.bin)

        self.q.joined_tables = ['TubeCases', 'PmtHistos', 'PmtTubeCases']
        self.__add_mods_to_query(**kwargs)

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

        self.q = self.session.query(TubeCases.date.label('date'),
                                    TubeCases.cytnum.label('cytnum'),
                                    PmtTubeCases.Antigen.label('Antigen_IN'),
                                    PmtTubeCases.Fluorophore.label('Fluorophore_IN'),
                                    PmtTubeCasesFROM.Antigen.label('Antigen_FROM'),
                                    PmtTubeCasesFROM.Fluorophore.label('Fluorophore_FROM'),
                                    PmtCompCorr).\
            join(PmtTubeCasesFROM, PmtCompCorr.PMT_FROM).\
            join(PmtTubeCases, PmtCompCorr.PMT_IN).\
            join(TubeCases, PmtTubeCases.Tube)

        self.q.joined_tables = ['TubeCases', 'PmtTubeCases', 'PmtTubeCasesIN', 'PmtCompCorr']

        self.__add_mods_to_query(**kwargs)

        df = self.__q2df()
        return df

    def __getCreationDate(self, **kwargs):
        """ Returns creation_date of db """
        log.info('Looking for db creation_date')
        self.q = self.session.query(MetaTable)
        d = self.q.one().creation_date
        return d

    def __delCasesByCustom(self, **kwargs):
        """ Deletes cases not in the CustomCaseData

        NOTE: Currently using session.delete() to make use of in-python CASCADE DELETION.
        This is likely much slower than self.q.delete() would, but I would have to turn on the the
        passive and set ON DELETE CASCADE on the foreign_keys [TODO]
        """

        log.info('Excluding cases not in CustomCaseData table')

        self.q = self.session.query(Cases).\
                 outerjoin(CustomCaseData, Cases.CustomData).\
                 filter(CustomCaseData.category == None)
        for case in self.q:
            self.session.delete(case)
        self.session.commit()

    def __delCases(self, cases, **kwargs):
        """ Delete cases passed in <cases>

        cases -- list()

        NOTE: Currently using session.delete() to make use of in-python CASCADE DELETION.
        This is likely much slower than self.q.delete() would, but I would have to turn on the the
        passive and set ON DELETE CASCADE on the foreign_keys [TODO]
        """
        log.info('Excluding from db cases [{}]'.format(cases))

        self.q = self.session.query(Cases).\
                 filter(Cases.case_number.in_(cases))
        for case in self.q:
            self.session.delete(case)
        self.session.commit()

    def __delTubeCases(self, case_tube_idxs, **kwargs):
        """ Delete case_tubes passed in <cases>

        cases -- list()

        NOTE: Currently using session.delete() to make use of in-python CASCADE DELETION.
        This is likely much slower than self.q.delete() would, but I would have to turn on the the
        passive and set ON DELETE CASCADE on the foreign_keys [TODO]
        """
        log.info('Excluding case_tube_idx [{}]'.format(case_tube_idxs))

        self.q = self.session.query(TubeCases).\
                 filter(TubeCases.case_tube_idx.in_(case_tube_idxs))
        for case_tube in self.q:
            self.session.delete(case_tube)
        self.session.commit()

    def __updateProblemTubeCases(self, df, **kwargs):
        """ For each case_tube_idx listed update its error_message and flag based on df

        df -- DataFrame with columns 'case_tube_idx' and 'error_message' and 'flag'

        NOTE: df.case_tube_idx must be unique
        """
        log.info('Flagging case_tube_idxs because of {}'.format(df.flag.tolist()))

        case_tube_idx_to_change = df.case_tube_idx.tolist()
        self.q = self.session.query(TubeCases).\
                 filter(TubeCases.case_tube_idx.in_(case_tube_idx_to_change))
        for case_tube in self.q:
            row_mask = df.case_tube_idx == case_tube.case_tube_idx
            case_tube.flag = df.loc[row_mask, 'flag'].tolist()[0]
            case_tube.error_message = str(df.loc[row_mask, 'error_message'].tolist()[0])

        self.session.commit()

    def __add_mods_to_query(self, **kwargs):
        """ Add filters specified in kwargs to q

        Keyword arguments:
        tubes -- <list> Select set based on tube types
        daterange -- <list> [X,X] Select set based on date between daterange
        """
        self.q = add_mods_to_query(self.q, **kwargs)

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


def add_mods_to_query(q, **kwargs):
    if 'not_flagged' in kwargs and kwargs['not_flagged'] is True:
        q = q.filter(TubeCases.flag == 'GOOD')
        if 'TubeCases' not in q.joined_tables:
            q = q.join(TubeCases)

    if 'tubes' in kwargs and kwargs['tubes'] is not None:
        tubes_to_select = [unicode(x) for x in kwargs['tubes']]
        log.info('Looking for tubes: %s' % tubes_to_select)
        q = q.filter(TubeTypesInstances.tube_type.in_(tubes_to_select))
        if 'TubeTypesInstances' not in q.joined_tables:
            q = q.join(TubeTypesInstances)

    if 'antigens' in kwargs and kwargs['antigens'] is not None:
        antigens_to_select = [unicode(x) for x in kwargs['antigens']]
        log.info('Looking for antigens: %s' % antigens_to_select)
        q = q.filter(PmtTubeCases.Antigen.in_(antigens_to_select))
        if 'PmtTubeCases' not in q.joined_tables:
            q = q.join(PmtTubeCases)

    if 'daterange' in kwargs and kwargs['daterange'] is not None:
        log.info('Looking for daterange: [%s, %s]' % (kwargs['daterange'][0],
                                                      kwargs['daterange'][1]))
        date_start = datetime.strptime(kwargs['daterange'][0], '%Y-%m-%d')
        date_end = datetime.strptime(kwargs['daterange'][1], '%Y-%m-%d')
        q = q.filter(func.date(TubeCases.date).between(date_start, date_end))
        if 'TubeCases' not in q.joined_tables:
            q = q.join(TubeCases)

    if 'cases' in kwargs and kwargs['cases'] is not None:
        cases_to_select = [unicode(x) for x in kwargs['cases']]
        log.info('Looking for cases #%s' % ", ".join(cases_to_select))
        q = q.filter(TubeCases.case_number.in_(cases_to_select))
        if 'TubeCases' not in q.joined_tables:
            q = q.join(TubeCases)

    if 'cytnum' in kwargs and kwargs['cytnum'] is not None:
        cytnums_to_select = [unicode(x) for x in kwargs['cytnum']]
        log.info('Looking for cytnum #%s' % ", ".join(cytnums_to_select))
        q = q.filter(TubeCases.cytnum.in_(cytnums_to_select))
        if 'TubeCases' not in q.joined_tables:
            q = q.join(TubeCases)

    if 'case_tube_idxs' in kwargs and kwargs['case_tube_idxs'] is not None:
        case_tube_idxs_to_select = [int(x) for x in kwargs['case_tube_idxs']]
        log.info('Looking for case_tube_idxs #{}'.format(case_tube_idxs_to_select))
        q = q.filter(TubeCases.case_tube_idx.in_(case_tube_idxs_to_select))
        if 'TubeCases' not in q.joined_tables:
            q = q.join(TubeCases)

    if 'custom_set' in kwargs and kwargs['custom_set'] is not None:
        q = q.join(CustomCaseData)

    if 'random_order' in kwargs and kwargs['random_order'] is True:
        q = q.order_by(func.random())
    elif 'date_order' in kwargs and kwargs['date_order'] is True:
        q = q.order_by(func.datetime(TubeCases.date))
        if 'TubeCases' not in q.joined_tables:
            q = q.join(TubeCases)

    if 'record_n' in kwargs and kwargs['record_n'] is not None:
        q = q.limit(kwargs['record_n'])

    return q
