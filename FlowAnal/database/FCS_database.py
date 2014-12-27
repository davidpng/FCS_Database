""" Class for FCS database """

import logging
import pandas as pd
from inspect import getsourcelines
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

from hsqr.database.database import SqliteConnection

from query_database import queryDB
from FlowAnal.__init__ import package_data
from FlowAnal.database.FCS_declarative import *


log = logging.getLogger(__name__)


class FCSdatabase(SqliteConnection):
    """ Object interface for Flow cytometry database

    Provides an object for FCS database, inheriting from general
    SqliteConnection
    """

    def __init__(self, db, interrupt=5, rebuild=False, build='alchemy'):
        log.debug('initializing FCSdatabase')
        self.tables = ['PmtTubeCases', 'TubeCases', 'Cases', 'TubeTypesInstances',
                       'Antigens', 'Fluorophores']
        super(FCSdatabase, self).__init__(db=db, tables=self.tables, build=build)

        if build == 'sql' and rebuild is True:
            self.create()
        elif build == 'alchemy':
            self.create_alchem(rebuild=rebuild)

    def create_alchem(self, rebuild=False):
        """ Drop and recreate FCS database from sqlalchemy statements """

        Base.metadata.bind = self.engine
        if rebuild is True:
            log.info("Dropping existing data in DB [%s]" % self.db_file)
            Base.metadata.drop_all()

        Base.metadata.create_all()

        if self.enforce_foreign_keys:
            self.enforce_foreign_keys()
        self.meta = Base.metadata

        self.insp = inspect(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        self.engine.conn = self.engine.connect()
        self.engine.conn.execute("ANALYZE")

    def create(self, files=['setup_hpmeta.sql']):
        """ Drop and recreate FCS database from <files> """
        self.drop_all()
        for file in files:
            self.run_sql_file(file, dir='FlowAnal/database/sqlite')
        self.engine.conn.execute("ANALYZE")

    def query(self, out_file=None, exporttype='dict_dict', **kwargs):
        """ Query database and return results according to <exporttype>

        Keyword arguments:
        exporttype -- ['dict_dict', 'df']
        outfile -- file to write out a pandas dataframe

        Optional arguments:
        getfiles -- Use queryDB.getfiles() to find files based on criteria
        tubes -- <list> Select set based on tube types
        daterange -- <list> [X,X] Select set based on date between daterange
        """
        if out_file:
            q = queryDB(self, exporttype='df', **kwargs)
            q.results.to_csv(out_file, index=False, index_label=None, encoding='utf-8')
            return 0
        else:
            return queryDB(self, exporttype=exporttype, **kwargs)

    def exportTubeTypes(self, **kwargs):
        """ Export TubeTypesInstances to csv (for review) """

        a = self.sql2pd(table='TubeTypesInstances')

        out_file = 'FlowAnal/data/tube_types.tmp'
        if kwargs['file'] is not None:
            out_file = kwargs['file']

        try:
            a.to_csv(out_file, index=False)
            log.info('Exported TubeTypesInstances to data/tube_types.tmp')
        except:
            raise 'Failed to export'

    def importTubeTypes(self, **kwargs):
        """
        Import TubeTypesInstances from csv and overwrite existing TubeTypeInstances
        and TubeTypes tables in db
        """

        # Load csv file
        in_file = package_data(fname='tube_types.csv')
        if kwargs['file'] is not None:
            in_file = kwargs['file']
        a = pd.read_csv(in_file)

        # Replace tubeTypes
        s = self.Session()
        self.meta.tables['TubeTypes'].delete()
        print "WARNING: deletion of TubeTypes not working currently (TODO)"
        s.close()
        tube_types = list(a.tube_type.unique())
        self.add_list(tube_types, 'TubeTypes')

        # Replace TubeTypesInstances
        s = self.Session()
        self.meta.tables['TubeTypesInstances'].delete()
        s.close()
        self.add_df(df=a, table='TubeTypesInstances')
