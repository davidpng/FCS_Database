import logging
log = logging.getLogger(__name__)
import pandas as pd
from hsqr.lab_pred import Lab_pred_table


class Cyto_table(Lab_pred_table):
    """
    Child class to handle "AML Cyto data" table
    """
    def __init__(self, db, file=None, pt_id=['MRN']):
        super(Cyto_table, self).__init__(db=db)
        self.pt_id = pt_id

        if file is not None:
            self.file = file
            self.__load_from_file(file=file)
            self.__process_dat()
        else:
            self.__load_from_db()

    def __load_from_file(self, file):
        """ Load in csv data to self.dat """

        self.dat = pd.read_csv(file, sep="\t", encoding="ISO-8859-1")

    def __process_dat(self):
        """ Make some changes to a newly loaded hemepathdb from csv """

        self.dat.rename(columns={'UW_Id': 'MRN',
                                 'AccessionNumber': 'AccNum',
                                 'SampleCollectionDate': 'CollDate',
                                 'SampleReceivedDate': 'RecDate'},
                        inplace=True)

    def __load_from_db(self):
        """ Load in data from sql database """

        self.dat = self.get_table(table='AML_Cyto')

    def push_to_db(self):
        """ Push data to sqlite db """

        log.info('Pushing file {} to db {}'.format(self.file,
                                                   self.db.db_file))
        # Add patients to the full case list
        self.db.add_list(x=self.dat.MRN.tolist(), table='Patients')

        # Add data table to HPdb table
        self.db.add_df(df=self.dat, table='AML_Cyto')
