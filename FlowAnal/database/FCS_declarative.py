from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, \
    create_engine, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.schema import ForeignKeyConstraint


class Base(object):
    @declared_attr
    def __init__(self):
        super(Base, self).__init__()

Base = declarative_base(cls=Base)


class SingleComp(Base):
    __tablename__ = 'SingleComp'

    comp_tube_idx = Column(Integer, primary_key=True)
    date = Column(DateTime)
    cytnum = Column(String(3))
    Antigen = Column(String(10), ForeignKey('Antigens.Antigen'))
    Fluorophore = Column(String(10), ForeignKey('Fluorophores.Fluorophore'))
    Channel_Name = Column(String(20), nullable=False)
    Channel_Number = Column(Integer, nullable=False)
    xt_Channel_Number = Column(Integer, nullable=False, primary_key=True)
    m = Column(Float)
    b = Column(Float)
    N = Column(Integer)
    score = Column(Float)
    old = Column(String(5))
    filename = Column(String(100), nullable=False)
    dirname = Column(String(255), nullable=False)

Index('ix_SingleComp', SingleComp.date, SingleComp.cytnum,
      SingleComp.Channel_Name, SingleComp.old, SingleComp.xt_Channel_Number,
      SingleComp.filename, SingleComp.dirname, unique=True)


class PmtTubeCases(Base):
    __tablename__ = 'PmtTubeCases'

    case_tube_idx = Column(Integer, ForeignKey('TubeCases.case_tube_idx'), primary_key=True)
    Antigen = Column(String(10), ForeignKey('Antigens.Antigen'))
    Fluorophore = Column(String(10), ForeignKey('Fluorophores.Fluorophore'))
    Channel_Name = Column(String(20), nullable=False)
    Channel_Number = Column(Integer, nullable=False, primary_key=True)
    Short_name = Column(String(20))
    Bits = Column(Integer)
    Amp_type = Column(String(10))
    Amp_gain = Column(Float)
    Range = Column(Integer)
    Voltage = Column(Integer)
    version = Column(String(30), nullable=False)

# Relations: PmtHistos, Tube, PmtStats, PmtCompCorr_IN, PmtCompCorr_FROM

Index('ix_PmtTubeCases_idx', PmtTubeCases.case_tube_idx, PmtTubeCases.Antigen,
      PmtTubeCases.Fluorophore, unique=True)
Index('ix_PmtTubeCases_Antigen', PmtTubeCases.Antigen, PmtTubeCases.Fluorophore)
Index('ix_PmtTubeCases_Channel', PmtTubeCases.Channel_Number)
Index('ix_PmtTubeCases_Fluo', PmtTubeCases.Fluorophore)


class TubeCases(Base):
    __tablename__ = 'TubeCases'
    case_tube_idx = Column(Integer, primary_key=True)
    case_tube = Column(String(100), nullable=False)
    filename = Column(String(100), nullable=False)
    dirname = Column(String(255), nullable=False)
    case_number = Column(String(10),
                         ForeignKey('Cases.case_number'), nullable=False)
    tube_type_instance = Column(Integer, ForeignKey('TubeTypesInstances.tube_type_instance'))
    date = Column(DateTime)
    num_events = Column(Integer)
    cytometer = Column(String(10))
    cytnum = Column(String(3))
    flag = Column(String(30), nullable=False)
    error_message = Column(Text)
    version = Column(String(30), nullable=False)

    Pmts = relationship("PmtTubeCases", backref="Tube", cascade='delete, delete-orphan')
    Stats = relationship("TubeStats", uselist=False, backref="Tube")

Index('ix_TubeCases_case_num', TubeCases.case_number)
Index('ix_TubeCases_date_cytnum', TubeCases.date, TubeCases.cytnum)
Index('ix_TubeCases_file', TubeCases.filename, TubeCases.dirname)  # , unique=True)
Index('ix_TubeCases_tube_type_instance', TubeCases.tube_type_instance)


class Cases(Base):
    __tablename__ = 'Cases'
    case_number = Column(String(10), primary_key=True)

    Tubes = relationship("TubeCases", backref='Case', cascade='delete, delete-orphan')
    HPdb = relationship("HPdb", backref='Case', cascade='delete, delete-orphan')


class CustomCaseData(Base):
    __tablename__ = 'CustomCaseData'
    case_number = Column(String(10), ForeignKey('Cases.case_number'),
                         nullable=False, primary_key=True)
    category = Column(String(30))

    Cases = relationship("Cases", uselist=False, backref='CustomData')


class HPdb(Base):
    __tablename__ = 'HPdb'

    id_pat = Column(Integer)
    case_number = Column(String(10),
                         ForeignKey('Cases.case_number'),
                         primary_key=True)
    case_type = Column(String(3), primary_key=True)
    AccNum = Column(String(50))
    MRN = Column(String(50), ForeignKey('Patients.MRN'))
    LastName = Column(String(50))
    FirstName = Column(String(50))
    DOB = Column(String(50))
    SpecimenType = Column(String(30))
    CollDate = Column(String(50))
    Hospital = Column(String(50))
    ReportType = Column(String(30))
    Clinicalinfo = Column(Text)
    Diagnosis = Column(Text)
    Sex = Column(String(10))
    LISSpecimen = Column(String(50))
    SpecimenID = Column(String(50))
    RecDtTm = Column(DateTime)
    FirstMiddleName = Column(String)
    MiddleName = Column(String)
    FullNameSorted = Column(String)

Index('ix_HPdb_patient_test', HPdb.MRN, HPdb.AccNum)
Index('ix_HPdb_RecDtTm', HPdb.RecDtTm)


class LISdb(Base):
    __tablename__ = 'LISdb'
    TestId = Column(Integer, primary_key=True)
    MRN = Column(String(50), ForeignKey('Patients.MRN'))
    PatName = Column(String(255))
    DOB = Column(DateTime)
    Sex = Column(String(10))
    PatLoc = Column(String(30))
    Facility = Column(String(30))
    LocType = Column(String(30))
    Login_Loc = Column(String(30))
    Ord_comment = Column(String(30))
    Priority = Column(String(30))
    OrdDoc = Column(String(50))
    OrdDoc_Name = Column(String(50))
    CollDate = Column(DateTime)
    CollTime = Column(DateTime)
    RecDate = Column(DateTime)
    RecTime = Column(DateTime)
    ResDate = Column(DateTime)
    ResTime = Column(DateTime)
    CollDtTm = Column(DateTime)
    RecDtTm = Column(DateTime)
    ResDtTm = Column(DateTime)
    AccNum = Column(String(10))
    PackCode = Column(String(20))
    PackName = Column(String(50))
    BattCode = Column(String(20))
    BattName = Column(String(50))
    TestCode = Column(String(10))
    TestName = Column(String(30))
    Result = Column(String(30))
    Addl_Result = Column(String(50))
    Units = Column(String(10))

    __table_args__ = (ForeignKeyConstraint(['MRN', 'AccNum'],
                                           ['HPdb.MRN',
                                            'HPdb.AccNum'],
                                           name='fk_LISdb_HPdb'),)

    HPdb = relationship("HPdb", uselist=False,
                        foreign_keys=[MRN, AccNum],
                        backref='LISdb')

Index('ix_LISdb_test_type', LISdb.TestCode)
Index('ix_LISdb_patient_test', LISdb.MRN, LISdb.AccNum)
Index('ix_LISdb_RecDtTm', LISdb.RecDtTm)


class AML_Cyto(Base):
    __tablename__ = 'AML_Cyto'
    AML_CytogeneticsId = Column(Integer, primary_key=True)
    MRN = Column(String(20), ForeignKey('Patients.MRN'))
    PtName = Column(String(150))
    AML_DxDate = Column(DateTime)
    ArrivalDate = Column(DateTime)
    PtDOD = Column(DateTime)
    DLC = Column(DateTime)
    CytoComment = Column(String(2000))
    CollDate = Column(DateTime)
    RecDate = Column(DateTime)
    SampleSource = Column(String(150))
    SWOG_Category = Column(String(255))
    CytoRisk = Column(String(255))
    CytoData = Column(String(2000))
    CleanedDataCyto = Column(String(2000))
    FISH_Summary = Column(String(2000))
    Others = Column(String(2000))
    FISH = Column(String(2000))
    AccNum = Column(String(20))
    ReportSource = Column(String(50))

Index('ix_AML_Cyto_patient_test', AML_Cyto.MRN, AML_Cyto.AccNum)
Index('ix_AML_Cyto_RecDate', AML_Cyto.RecDate)
Index('ix_AML_Cyto_Cyto', AML_Cyto.CytoRisk)
Index('ix_AML_Cyto_SWOG', AML_Cyto.SWOG_Category)


class Patients(Base):
    __tablename__ = 'Patients'
    MRN = Column(String(50), primary_key=True)

    HPdb = relationship("HPdb", backref='Patient', cascade='delete, delete-orphan')
    LISdb = relationship("LISdb", backref='Patient', cascade='delete, delete-orphan')
    AML_Cyto = relationship("AML_Cyto", backref='Patient', cascade='delete, delete-orphan')


class TubeTypesInstances(Base):
    __tablename__ = 'TubeTypesInstances'
    tube_type_instance = Column(Integer, primary_key=True)
    tube_type = Column(String(20), ForeignKey('TubeTypes.tube_type'), nullable=False)
    Antigens = Column(String(255), nullable=False)

    Tubes = relationship("TubeCases", backref="TubeTypesInstance")

Index('ix_TubeTypesInstances_tube_type', TubeTypesInstances.tube_type)
Index('ix_TubeTypesInstances_Antigens', TubeTypesInstances.Antigens)


class TubeTypes(Base):
    __tablename__ = 'TubeTypes'
    tube_type = Column(String(20), primary_key=True)


class Antigens(Base):
    __tablename__ = 'Antigens'
    Antigen = Column(String(10), primary_key=True)


class Fluorophores(Base):
    __tablename__ = 'Fluorophores'
    Fluorophore = Column(String(10), primary_key=True)


class TubeStats(Base):
    __tablename__ = 'TubeStats'
    case_tube_idx = Column(Integer, ForeignKey('TubeCases.case_tube_idx'), primary_key=True)
    total_events = Column(Integer, nullable=False)
    transform_not_nan = Column(Integer, nullable=False)
    transform_in_limits = Column(Integer, nullable=False)
    viable_remain = Column(Integer)
    singlet_remain = Column(Integer)
    version = Column(String(30), nullable=False)

    # Relations: Tube


class PmtStats(Base):
    __tablename__ = 'PmtStats'
    case_tube_idx = Column(Integer, nullable=False, primary_key=True)
    Channel_Number = Column(Integer, nullable=False, primary_key=True)
    count = Column(Integer)
    mean = Column(Float)
    std = Column(Float)
    min = Column(Float)
    X25 = Column(Float)
    median = Column(Float)
    X75 = Column(Float)
    max = Column(Float)
    transform_not_nan = Column(Integer)
    transform_in_limits = Column(Integer)

    __table_args__ = (ForeignKeyConstraint(['case_tube_idx', 'Channel_Number'],
                                           ['PmtTubeCases.case_tube_idx',
                                            'PmtTubeCases.Channel_Number'],
                                           name='fk_PmtStats_PmtTubeCases'),)

    Pmt = relationship("PmtTubeCases", uselist=False,
                       foreign_keys=[case_tube_idx, Channel_Number],
                       backref='PmtStats')

Index('ix_PmtStats_Channel_Number', PmtStats.Channel_Number)


class Beads8peaks(Base):
    __tablename__ = 'Beads8peaks'
    id = Column(Integer, primary_key=True)
    Fluorophore = Column(String(20), nullable=False)  # , primary_key=True)
    cytnum = Column(String(3), nullable=False)  # primary_key=True)
    date = Column(String(20), nullable=False)  # primary_key=True)
    peak = Column(String(2), nullable=False)  # primary_key=True)
    MFI = Column(Float)

Index('ix_Beads8peaks_all', Beads8peaks.cytnum, Beads8peaks.Fluorophore,
      Beads8peaks.peak, Beads8peaks.date)


class BeadsUltra(Base):
    __tablename__ = 'BeadsUltra'
    id = Column(Integer, primary_key=True)
    Fluorophore = Column(String(20), nullable=False)  # , primary_key=True)
    cytnum = Column(String(3), nullable=False)  # primary_key=True)
    date = Column(String(20), nullable=False)  # primary_key=True)
    Mean = Column(Integer)
    CV = Column(Float)

Index('ix_BeadsUltra_all', BeadsUltra.cytnum, BeadsUltra.Fluorophore,
      BeadsUltra.date)


class PmtHistos(Base):
    __tablename__ = 'PmtHistos'
    case_tube_idx = Column(Integer, nullable=False, primary_key=True)
    Channel_Number = Column(Integer, nullable=False, primary_key=True)
    bin = Column(String(20), nullable=False, primary_key=True)
    density = Column(Float)

    __table_args__ = (ForeignKeyConstraint(['case_tube_idx', 'Channel_Number'],
                                           ['PmtTubeCases.case_tube_idx',
                                            'PmtTubeCases.Channel_Number'],
                                           name='fk_PmtHistos_PmtTubeCases'),)

    Pmt = relationship("PmtTubeCases", uselist=False,
                       foreign_keys=[case_tube_idx, Channel_Number],
                       backref='PmtHistos')

Index('ix_PmtHistos', PmtHistos.Channel_Number, PmtHistos.bin)


class PmtCompCorr(Base):
    __tablename__ = 'PmtCompCorr'
    case_tube_idx = Column(Integer, nullable=False, primary_key=True)
    Channel_Number_IN = Column(Integer, nullable=False, primary_key=True)
    Channel_Number_FROM = Column(Integer, nullable=False, primary_key=True)
    Pearson_R = Column(Float)
    P_value = Column(Float)

    __table_args__ = (ForeignKeyConstraint(['case_tube_idx', 'Channel_Number_IN'],
                                           ['PmtTubeCases.case_tube_idx',
                                            'PmtTubeCases.Channel_Number'],
                                           name='fk_PmtCompCorr_IN'),
                      ForeignKeyConstraint(['case_tube_idx', 'Channel_Number_FROM'],
                                           ['PmtTubeCases.case_tube_idx',
                                            'PmtTubeCases.Channel_Number'],
                                           name='fk_PmtCompCorr_FROM'))

    PMT_IN = relationship("PmtTubeCases",
                          foreign_keys=[case_tube_idx, Channel_Number_IN],
                          uselist=False, backref='CompCorr_IN')
    PMT_FROM = relationship("PmtTubeCases",
                            foreign_keys=[case_tube_idx, Channel_Number_FROM],
                            uselist=False, backref='CompCorr_FROM')

Index('ix_PmtCompCorr_IN_FROM', PmtCompCorr.Channel_Number_IN, PmtCompCorr.Channel_Number_FROM)
Index('ix_PmtCompCorr_FROM_IN', PmtCompCorr.Channel_Number_FROM, PmtCompCorr.Channel_Number_IN)


class MetaTable(Base):
    __tablename__ = 'MetaTable'
    creation_date = Column(DateTime, nullable=False, primary_key=True)


class full_PmtHistos(Base):
    __tablename__ = 'full_PmtHistos'

    case_tube_idx = Column(Integer, primary_key=True)
    cytnum = Column(String(3))
    date = Column(DateTime)
    Antigen = Column(String(10))
    Fluorophore = Column(String(10))
    Channel_Name = Column(String(20), nullable=False)
    Channel_Number = Column(Integer, nullable=False, primary_key=True)
    tube_type_instance = Column(Integer)
    tube_type = Column(String(20), nullable=False)
    bin = Column(Float, primary_key=True)
    density = Column(Float)

Index('ix_full_PmtHistos_name_tube', full_PmtHistos.Channel_Name,
      full_PmtHistos.tube_type)
Index('ix_full_PmtHistos_Antigen_tube', full_PmtHistos.Antigen,
      full_PmtHistos.tube_type)
Index('ix_full_PmtHistos_channel_tube', full_PmtHistos.Channel_Number,
      full_PmtHistos.tube_type)


if __name__ == '__main__':
    sqlalchemy = 'sqlite:////home/local/AMC/hermands/repos/flow_anal/db/test_alchemy.db'
    engine = create_engine(sqlalchemy)
    Base.metadata.create_all(engine)
