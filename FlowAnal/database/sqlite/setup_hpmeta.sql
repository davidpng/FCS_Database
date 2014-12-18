-- Create tables and constraints for hematopathology flow cytometry
-- meta information
-- index name convention is ix_<table>_<column1>[_<column2>...]

--PRAGMA foreign_keys = ON;

-- Case_Tube_Pmt
CREATE TABLE IF NOT EXISTS PmtTubeCases (
       case_tube NVARCHAR(100) NOT NULL,
       Antigen NVARCHAR(10) NOT NULL,
       Fluorophore NVARCHAR(10) NOT NULL,
       "Channel Name" NVARCHAR(20),
       "Channel Number" INTEGER,
       "Short name" NVARCHAR(20),
       "Bits" INTEGER,
       "Amp type" NVARCHAR(10),
       "Amp gain" REAL,
       "Range" INTEGER,
       Voltage INTEGER,
       version VARCHAR(30) NOT NULL,
       PRIMARY KEY (case_tube, "Channel Name"),
       FOREIGN KEY (case_tube) REFERENCES TubeCases(case_tube),
       FOREIGN KEY (Antigen) REFERENCES Antigens(Antigen),
       FOREIGN KEY (Fluorophore) REFERENCES Fluorophores(Fluorophore)
);
CREATE INDEX IF NOT EXISTS ix_PmtTubeCases_case_tube_antigen_fluor
       ON PmtTubeCases (case_tube, Antigen, Fluorophore);
CREATE INDEX IF NOT EXISTS ix_PmtTubeCases_antigen_fluor
       ON PmtTubeCases (Antigen, Fluorophore);
CREATE INDEX IF NOT EXISTS ix_PmtTubeCases_number
       ON PmtTubeCases ("Channel Number");
CREATE INDEX IF NOT EXISTS ix_PmtTubeCases_antigen_number
       ON PmtTubeCases (Antigen, "Channel Number");

-- Tube experiment
CREATE TABLE IF NOT EXISTS TubeCases (
       case_tube NVARCHAR(100) PRIMARY KEY,
       filename NVARCHAR(100) NOT NULL,
       dirname NVARCHAR(255) NOT NULL,
       case_number NVARCHAR(10) NOT NULL,
       tube_type_instance INTEGER,
       date DATETIME,
       num_events INTEGER,
       cytometer NVARCHAR(10),
       cytnum INTEGER,
       empty BOOLEAN,
       version VARCHAR(30) NOT NULL,
       CONSTRAINT empty_bool CHECK ("empty" IN (0, 1)),
       FOREIGN KEY (case_number) REFERENCES Cases(case_number),
       FOREIGN KEY (tube_type_instance) REFERENCES TubeTypesInstances(tube_type_instance)
);
CREATE INDEX IF NOT EXISTS ix_TubeCases_case_number
       ON TubeCases (case_number);
CREATE INDEX IF NOT EXISTS ix_TubeCases_date
       ON TubeCases (date);

CREATE TABLE IF NOT EXISTS Cases (
       case_number NVARCHAR(10) PRIMARY KEY
);

-- Tube types
CREATE TABLE IF NOT EXISTS TubeTypesInstances (
       tube_type_instance INTEGER PRIMARY KEY,
       tube_type NVARCHAR(20) NOT NULL,
       Antigens NVARCHAR(255) NOT NULL,
       FOREIGN KEY (tube_type) REFERENCES TubeTypes (tube_type)
);
CREATE INDEX IF NOT EXISTS ix_TubeTypesInstances_tube_type
       ON TubeTypesInstances(tube_type);
CREATE INDEX IF NOT EXISTS ix_TubeTypesInstances_antigen
       ON TubeTypesInstances(Antigens);
CREATE TABLE IF NOT EXISTS TubeTypes (
       tube_type NVARCHAR(20) PRIMARY KEY
);

-- Antigens
CREATE TABLE IF NOT EXISTS Antigens (
       Antigen NVARCHAR(10) PRIMARY KEY
);

-- Fluorophores
CREATE TABLE IF NOT EXISTS Fluorophores (
       Fluorophore NVARCHAR(10) PRIMARY KEY
);

-- Pmt event stats
CREATE TABLE IF NOT EXISTS PmtStats (
       case_tube NVARCHAR(100) NOT NULL,
      "Channel Name" NVARCHAR(20) NOT NULL,
       count INTEGER,
       mean FLOAT,
       std FLOAT,
       min FLOAT,
       "25%" FLOAT,
       "50%" FLOAT,
       "75%" FLOAT,
       max FLOAT,
       transform_remain INTEGER,
       version VARCHAR(30) NOT NULL,
       PRIMARY KEY (case_tube, "Channel Name"),
       FOREIGN KEY (case_tube) REFERENCES TubeCases (case_tube)
);

CREATE INDEX IF NOT EXISTS ix_PmtStats_Channel_Name
       ON PmtStats ("Channel Name");

-- Tube event stats
CREATE TABLE IF NOT EXISTS TubeStats (
       case_tube NVARCHAR(100) NOT NULL,
       total_events INTEGER NOT NULL,
       transform_remain INTEGER NOT NULL,
       viable_remain INTEGER NULL,
       singlet_remain INTEGER NULL,
       version VARCHAR(30) NOT NULL,
       PRIMARY KEY (case_tube),
       FOREIGN KEY (case_tube) REFERENCES TubeCases (case_tube)
);

-- Pmt event histogram
CREATE TABLE IF NOT EXISTS PmtHistos (
       case_tube NVARCHAR(100) NOT NULL,
       "Channel Name" NVARCHAR(20) NOT NULL,
       bin NVARCHAR(20) NOT NULL,
       density FLOAT,
       PRIMARY KEY (case_tube, "Channel Name", bin),
       FOREIGN KEY (case_tube, "Channel Name") REFERENCES PmtTubeCases (case_tube, "Channel Name")
);
CREATE INDEX IF NOT EXISTS PmtHistos_bin
       ON PmtHistos (bin);
CREATE TABLE IF NOT EXISTS HistoBins (
       bin NVARCHAR(20) NOT NULL PRIMARY KEY);
