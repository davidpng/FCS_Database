import logging
log = logging.getLogger(__name__)
import pandas as pd
import datetime

from hsqr.lab_pred import Lab_pred_table


def date_conv(a):
    try:
        d = datetime.datetime.strptime(a, '%m/%d/%Y').date()
    except:
        d = None
    return d


class HP_table(Lab_pred_table):
    """
    Child class to handle "HP database" table
    """
    def __init__(self, db, file=None, pt_id=['id_pat']):
        super(HP_table, self).__init__(db=db)
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

        self.dat.rename(columns={'PatientID': 'MRN',
                                 'LISAccession': 'AccNum',
                                 'DateCollected': 'CollDate',
                                 'DateReceived': 'RecDtTm',
                                 'BirthDate': 'DOB'},
                        inplace=True)

        self.__correct_case_number()
        self.__correct_specimen_type()
        self.__correct_colldate()

    def __correct_case_number(self):
        """ Fix HPAccession to case_number """

        dat = self.dat.copy()

        # Remove "HP" and rename to case_number
        dat['case_number'] = dat.HPAccession.apply(lambda x: x[2:])
        dat['case_type'] = dat.HPAccession.apply(lambda x: x[0:2])
        dat.drop(['HPAccession'], axis=1, inplace=True)

        # Spot fix
        dat.loc[(dat.case_number == 'HP13-21085') &
                (dat.Diagnosis.str.startswith('JAK2')), 'case_number'] = 'GR13-21085'

        self.dat = dat

    def __correct_specimen_type(self):
        """ Fix HP specimen type """

        a = self.dat.SpecimenType.copy()
        a[a == 'PB'] = 'Peripheral Blood'
        a[a == 'CSF'] = 'Cerebrospinal Fluid'
        a[a == 'BAL'] = 'Bronchoaleolar Lavage'
        a[a == 'Bone Marrow Biopsy'] = 'Bone Marrow Aspirate'

        self.dat.SpecimenType = a

    def __correct_colldate(self):
        """ Change format and check colldate format """

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

        self.dat = self.get_table(table='HPdb')

    def push_to_db(self):
        """ Push data to sqlite db """

        log.info('Pushing file {} to db {}'.format(self.file,
                                                   self.db.db_file))

        # Add patients
        pts = self.dat.MRN
        pts = pts.dropna()
        self.db.add_list(x=pts.tolist(), table='Patients')

        # Add cases to the full case list
        self.db.add_list(x=self.dat.case_number.tolist(), table='Cases')

        # Add data table to HPdb table
        self.db.add_df(df=self.dat, table='HPdb')
