import logging
import os
import subprocess

import sqlite3
import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.schema import MetaData, Index
from sqlalchemy.orm import sessionmaker

from FlowAnal.exceptions import OperationalError

log = logging.getLogger(__name__)


class Connection(object):

    """
    Base class for instantiating an API for database access. Methods
    defined here must be database-agnostic.
    """

    def __init__(self):
        log.debug('initializing Connection')

    def close(self):
        self.engine.close()

    def common_colnames(self, table_a, table_b):
        """
        Returns list of columns in both input tables
        """

        cols_a = self.get_colnames(table_a)
        cols_b = self.get_colnames(table_b)

        return [x for x in cols_a if x in cols_b]

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
        """ Return list of tables """
        self.load_sqlalchemy()
        return self.meta.tables.keys()

    def drop_table(self, table):
        """ Drop table """
        if table in self.get_table_names():
            t = self.meta.tables[table]
            t.drop()

    def drop_all(self):
        """ Drop all tables """
        if self.meta.bind:
            self.meta.drop_all()


class SqliteConnection(Connection):

    """
    Provides an API for operations using an sqlite database.
    Initialize with a list of tables that have already been
    copied locally.
    """

    def __init__(self, db, tables, enforce_foreign_keys=False, interrupt=5):
        super(SqliteConnection, self).__init__()
        log.debug('initializing SqliteConnection')
        self.table_names = tables
        self.db_file = db

        self.sqlalchemy = 'sqlite:///' + os.path.abspath(db)
        self.enforce_foreign_keys = enforce_foreign_keys
        self.engine = create_engine(self.sqlalchemy)
        self.Session = sessionmaker(bind=self.engine)
        self.meta = MetaData()
        self.connect_via_sqlalchemy()

    def connect_via_sqlalchemy(self):
        """ Setup sqlalchemy connection and reflection

        This should be run prior to accessing database via sqlalchemy and
        should also be run after a non-sqlalchemy process alters the database
        """

        self.engine.conn = self.engine.connect()
        if self.enforce_foreign_keys:
            self.enforce_foreign_keys()
        self.meta.reflect(bind=self.engine)
        self.insp = inspect(self.engine)

    def enforce_foreign_keys(self):
        """ Turn ON Sqlite enforcement of foreign keys  """
        self.engine.conn.execute("PRAGMA foreign_keys=ON")

    def import_febrl_csv(self, table, file):
        """ Import csv using external csvsql tool """

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
        """ Import csv from amalga using external csvsql tool"""
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

    def run_sql_file(self, sql_file, dir):
        """
        Create the database, dropping existing tables if exist
        NOTE: Using pysqlite because sqlalchemy does not support this
        """

        self.engine.conn.close()  # close sqlalchemy connetion

        # Use pysqlite to run .sql script
        dbcon = sqlite3.connect(self.db_file)
        dbcur = dbcon.cursor()
        try:
            with open(os.path.join(dir, sql_file)) as f:
                dbcur.executescript(f.read())
        except sqlite3.OperationalError, e:
            raise OperationalError(e)
        dbcon.close()

        self.connect_via_sqlalchemy()  # reset sqlchemy connection

    def import_amalga_tables(self, constraint_sql='setup_sqlite.sql'):
        """
        Run amalga .sql code to setup database
        """
        for table in self.table_names:
            self.import_amalga_csv(table)

        self.run_sql_file(constraint_sql)

    def get_colnames(self, table):
        """
        Return a list of column names for the named table.
        """
        columns = self.insp.get_columns(table)
        colnames = [col['name'] for col in columns]
        return colnames

    def update_db_coltable(self, x, table):
        """ Update a single column table with x

        Keyword arguments:
        x -- <tuple of tuples>
        table -- <str> Table (single column) to add values to
        """
        trans = self.engine.conn.begin()
        try:
            cmd = 'insert or replace into ' + table + ' values (?)'
            self.engine.conn.execute(cmd, x)
            trans.commit()
            log.debug("Successively imported to %s" % table)
        except:
            trans.rollback()
            raise

    def update_db_table(self, df, table):
        """ Update db table with pandas df

        NOTE: df keys and table columns must perfectly match

        Keyword arguments:
        df -- <pandas dataframe> Data to add
        table -- <str> table to which to add <df>
        """
        cols = ['"' + x + '"' for x in df.columns.values]
        dat = tuple(df.itertuples(index=False))

        trans = self.engine.conn.begin()
        try:
            cmd = 'insert or replace into ' + table + ' (%s)' % \
                  ', '.join(cols) + \
                  ' values (%s)' % ', '.join(['?'] * len(cols))
            self.engine.conn.execute(cmd, dat)
            trans.commit()
            log.debug("Successively imported to %s" % table)
        except:
            trans.rollback()
            raise

    def add_dict(self, d, table):
        """ Add dictionary values to database table

        NOTE: <d> can be missing keys in table columns

        Keyword arguments:
        d -- <dict> Single dict to add
        table -- <str> table to which to add <d>
        """

        table_cols = self.get_colnames(table)
        colnames = [col for col in table_cols if col in d]

        # Fill in missing
        for k in table_cols:
            if k not in colnames:
                d[k] = None

        trans = self.engine.conn.begin()
        try:
            col_string = ', '.join([':' + c for c in table_cols])
            cmd = 'insert or replace into ' + table + ' values (%s)' % col_string
            self.engine.conn.execute(cmd, d)
            trans.commit()
            log.debug("Successively imported to %s" % table)
        except:
            trans.rollback()
            raise

    def add_df(self, df, table):
        """ Add pandas df to database table

        NOTE: df keys and table columns may not perfectly match, but MUST overlap

        Keyword arguments:
        df -- <pandas dataframe>
        table -- <str> Table that should be added to
        """

        # Restrict to common columns
        colnames = [col for col in self.get_colnames(table) if col in list(df.columns.values)]
        df_o = df[colnames].drop_duplicates()

        # Update db
        self.update_db_table(df=df_o, table=table)

    def add_list(self, x, table):
        """ Add a list to a database column

        Keyword arguments:
        x -- <list> Values to add to single column table
        table -- <str> Table to add values to
        """
        # Pass tuple of tuples
        self.update_db_coltable(x=tuple(zip(x)), table=table)
