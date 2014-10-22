""" Class for FCS database """

import logging
from database import SqliteConnection

log = logging.getLogger(__name__)


class FCSdatabase(SqliteConnection):

    """
    Provides an object for FCS database, inheriting from general
    SqliteConnection
    """

    def __init__(self, db, interrupt=5):
        log.debug('initializing FCSdatabase')
        self.tables = None
        super(FCSdatabase, self).__init__(db=db, tables=self.tables)
