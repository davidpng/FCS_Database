""" Class for FCS database """

import logging
from database import SqliteConnection

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
