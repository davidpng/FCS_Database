import logging
import os
import subprocess

import sqlite3
import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.schema import MetaData, Index

from FCS_Database import package_data
from FCS_Database.exceptions import OperationalError

log = logging.getLogger(__name__)


class Connection(object):

    """
    Base class for instantiating an API for database access. Methods
    defined here must be database-agnostic.
    """

    def __init__(self):
        log.debug('initializing Connection')

    def close(self):
        self.conn.close()

    def common_colnames(self, table_a, table_b):
        """
        Returns list of columns in both input tables
        """

        cols_a = self.get_colnames(table_a)
        cols_b = self.get_colnames(table_b)

        return [x for x in cols_a if x in cols_b]

    def load_sqlalchemy(self):
        """
        Load sql data into sqlalchemy framework
        """
        self.meta = MetaData()
        self.meta.reflect(bind=self.engine)
        self.insp = inspect(self.engine)

    def sql2pd(self, table, verbose=False):
        """ Retrieve sqlite table as pandas dataframe """

        dat = pd.read_sql_table(table, self.engine)
        if verbose:
            print dat.iloc[1:10, :]
            print dat.dtypes
        return dat

    def add_index(self, name, table, cols):
        """ Add index to database with cols in *args """

        # Reload sqlalchemy reflection
        self.load_sqlalchemy()

        # Check if index already exists
        if name in self.insp.get_indexes(table):
            return

        # Point to table
        t = self.meta.tables[table]

        # Make list of table.col
        table_cols = [c for c in t.c if c.name in cols]

        # Create index
        i = Index(name, *table_cols)
        i.create(self.engine.conn)

    def get_table_names(self):
        """ List of tables """
        self.load_sqlalchemy()
        return self.meta.tables.keys()

    def drop_table(self, table):
        """ Drop table """
        if table in self.get_table_names():
            t = self.meta.tables[table]
            t.drop()


class SqliteConnection(Connection):

    """
    Provides an API for operations using an sqlite database.
    Initialize with a list of tables that have already been
    copied locally.
    """

    def __init__(self, db, tables, interrupt=5):
        super(SqliteConnection, self).__init__()
        log.debug('initializing SqliteConnection')
        self.conn = sqlite3.connect(db)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.interrupt = interrupt
        self.filename = db
        self.sqlalchemy = 'sqlite:///' + os.path.abspath(db)
        self.engine = create_engine(self.sqlalchemy)
        self.engine.conn = self.engine.connect()
        self.table_names = tables
        self.load_sqlalchemy()

    def run_sql_file(self, sql_file):
        """
        Create the database, dropping existing tables if exists
        """

        try:
            with open(package_data(sql_file)) as f:
                self.cur.executescript(f.read())
        except sqlite3.OperationalError, e:
            raise OperationalError(e)

    def import_febrl_csv(self, table, file):
        """ Import csv """

        # Import into sqlite db
        cmd = 'csvsql --db %s --insert --snifflimit 100000 \
        --table %s %s' % (self.sqlalchemy, table, file)

        log.debug(cmd)
        try:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            log.debug("Importing data: " + ",".join(p.communicate()))
        except:
            raise

    def import_amalga_csv(self, table, prefix='db/raw/dsh_CVDq_'):
        """ Import csv from amalga """
        file = prefix + table + '.csv'
        cmd = 'csvsql -d, -u3 -v --db %s --insert --snifflimit 100000 \
        --table %s %s' % (self.sqlalchemy,
                          table,
                          file)
        try:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            log.debug("Importing data: " + ",".join(p.communicate()))
        except:
            raise

    def import_amalga_tables(self, constraint_sql='setup_sqlite.sql'):
        """
        Load amalga data into sqldb
        """
        for table in self.table_names:
            self.import_amalga_csv(table)

        self.run_sql_file(constraint_sql)

    def import_LIS_tables(self, constraint_sql):
        pass

    def get_attrs(self, name='table'):
        """
        Return a list of database attribute names. `name` can be one
        of 'table', 'index', ...
        """

        assert name in {'table', 'index'}

        cmd = "SELECT name FROM sqlite_master WHERE type = ?"
        self.cur.execute(cmd, (name,))
        return [x[0] for x in self.cur.fetchall()]

    def get_colnames(self, table):
        """
        Return a list of column names for the named table.
        """

        self.cur.execute('PRAGMA table_info(%s)' % (table,))
        return [d['name'] for d in self.cur.fetchall()]
