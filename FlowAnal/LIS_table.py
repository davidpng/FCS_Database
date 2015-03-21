import logging
log = logging.getLogger(__name__)
import pandas as pd
import datetime
from hsqr.lab_pred import Lab_pred_table


class LIS_table(Lab_pred_table):
    """
    Child class to handle "LIS data" table
    """
    def __init__(self, db, file=None, pt_id=['MRN']):
        super(LIS_table, self).__init__(db=db)
        self.pt_id = pt_id

        if file is not None:
            self.file = file
            self.__load_from_file(file=file)
            self.__process_dat()
        else:
            self.__load_from_db()

    def __load_from_file(self, file):
        """ Load in csv data to self.dat """

        self.dat = pd.read_csv(file)

    def __process_dat(self):
        """ Make some changes to a newly loaded hemepathdb from csv """

        self.dat.rename(columns={'PatNum': 'MRN',
                                 'LISAccession': 'AccNum',
                                 'DateCollected': 'CollDate'},
                        inplace=True)

        self.__combine_dt_tm()

    def __combine_dt_tm(self):
        """ Combine dates and times together """
        def date_conv(a):
            try:
                d = datetime.datetime.strptime(a, '%m/%d/%y').date()
            except:
                d = None
            return d

        def time_conv(a):
            try:
                t = datetime.datetime.strptime(a, '%H:%M').time()
            except:
                t = None
            return t

        # Create DtTm for Received, Collected, and Resulted Dates and Times
        for x in ['Rec', 'Coll', 'Res']:

            d = self.dat.loc[:, x + 'Date'].apply(date_conv).tolist()
            t = self.dat.loc[:, x + 'Time'].apply(time_conv).tolist()
            dt = []
            for di, ti in zip(d, t):
                try:
                    tmp = datetime.datetime.combine(di, ti).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    try:
                        tmp = datetime.datetime.combine(di, datetime.time()).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        tmp = None
                dt.append(tmp)

            self.dat[x + 'DtTm'] = dt

        # Standardize format of CollDate
        cd_new = []
        colld = self.dat.CollDate.apply(date_conv).tolist()
        for cdi in colld:
            try:
                tmp = datetime.datetime.strftime(cdi, '%Y-%m-%d')
            except:
                tmp = None
            cd_new.append(tmp)
        self.dat.CollDate = cd_new

    def __load_from_db(self):
        """ Load in data from sql database """

        self.dat = self.get_table(table='LISdb')

    def push_to_db(self):
        """ Push data to sqlite db """

        log.info('Pushing file {} to db {}'.format(self.file,
                                                   self.db.db_file))
        # Add patients to the full case list
        self.db.add_list(x=self.dat.MRN.tolist(), table='Patients')

        # Add data table to HPdb table
        self.db.add_df(df=self.dat, table='LISdb')
