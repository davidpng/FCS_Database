""" Class for FCS database """

import logging
import pandas as pd

from database import SqliteConnection
from query_database import queryDB
from FCS_Database.utils import package_data

log = logging.getLogger(__name__)


class FCSdatabase(SqliteConnection):

    """
    Provides an object for FCS database, inheriting from general
    SqliteConnection
    """

    def __init__(self, db, interrupt=5, rebuild=False):
        log.debug('initializing FCSdatabase')
        self.tables = ['PmtTubeCases', 'TubeCases', 'Cases', 'TubeTypesInstances',
                       'Antigens', 'Fluorophores']
        super(FCSdatabase, self).__init__(db=db, tables=self.tables)

        if rebuild:
            self.create()

    def create(self, files=['setup_hpmeta.sql']):
        """ Drop and recreate FCS database """
        self.drop_all()
        for file in files:
            self.run_sql_file(file, dir='database/sqlite')
        self.engine.conn.execute("ANALYZE")

    def query(self, out_file=None, exporttype='dict_dict', **kwargs):
        """
        Query database based passed arguments
        If outfile is defined query and write out pandas dataframe
        Else query db and return result
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
        out_file = 'FCS_Database/data/tube_types.tmp'
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
        and TubeTypes tables
        """
        # Load csv file
        in_file = package_data(fname='tube_types.csv', dir='data')
        if kwargs['file'] is not None:
            in_file = package_data(fname=kwargs['file'])
        a = pd.read_csv(in_file)

        # Replace tubeTypes
        s = self.Session()
        self.meta.tables['TubeTypes'].delete()
        print "WARNING: deletion of TubeTypes not working currently"
        s.close()
        tube_types = list(a.tube_type.unique())
        self.add_list(tube_types, 'TubeTypes')

        # Replace TubeTypesInstances
        s = self.Session()
        self.meta.tables['TubeTypesInstances'].delete()
        s.close()
        self.add_df(df=a, table='TubeTypesInstances')
