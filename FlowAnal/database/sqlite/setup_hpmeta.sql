-- Create tables and constraints for hematopathology flow cytometry
-- meta information
-- index name convention is ix_<table>_<column1>[_<column2>...]

--PRAGMA foreign_keys = ON;

-- Case_Tube_Pmt
CREATE TABLE IF NOT EXISTS PmtTubeCases (
       case_tube_idx INTEGER NULL,  -- tmp fix SHOULD BE NOT NULL
       Antigen NVARCHAR(10) NULL,
       Fluorophore NVARCHAR(10) NULL,
       "Channel Name" NVARCHAR(20) NOT NULL,
       "Channel Number" INTEGER NOT NULL,
       "Short name" NVARCHAR(20),
       "Bits" INTEGER,
       "Amp type" NVARCHAR(10),
       "Amp gain" REAL,
       "Range" INTEGER,
       Voltage INTEGER,
       version VARCHAR(30) NOT NULL,
       PRIMARY KEY (case_tube_idx, "Channel Name"),
       FOREIGN KEY (case_tube_idx) REFERENCES TubeCases(case_tube_idx),
       FOREIGN KEY (Antigen) REFERENCES Antigens(Antigen),
       FOREIGN KEY (Fluorophore) REFERENCES Fluorophores(Fluorophore)
);
CREATE INDEX IF NOT EXISTS ix_PmtTubeCases_case_tube_idx_antigen_fluor
       ON PmtTubeCases (case_tube_idx, Antigen, Fluorophore);
CREATE INDEX IF NOT EXISTS ix_PmtTubeCases_antigen_fluor
       ON PmtTubeCases (Antigen, Fluorophore);
CREATE INDEX IF NOT EXISTS ix_PmtTubeCases_number
       ON PmtTubeCases ("Channel Number");
CREATE INDEX IF NOT EXISTS ix_PmtTubeCases_antigen_number
       ON PmtTubeCases (Antigen, "Channel Number");
CREATE INDEX IF NOT EXISTS ix_PmtTubeCases_fluor
       ON PmtTubeCases (Fluorophore);

-- Tube experiment
CREATE TABLE IF NOT EXISTS TubeCases (
       case_tube_idx INTEGER PRIMARY KEY,
       case_tube NVARCHAR(100) NOT NULL,
       filename NVARCHAR(100) NOT NULL,
       dirname NVARCHAR(255) NOT NULL,
       case_number NVARCHAR(10) NOT NULL,
       tube_type_instance INTEGER,
       date DATETIME,
       num_events INTEGER,
       cytometer NVARCHAR(10),
       cytnum VARCHAR(3) NOT NULL,
       empty BOOLEAN NOT NULL,
       version VARCHAR(30) NOT NULL,
       CONSTRAINT empty_bool CHECK ("empty" IN (0, 1)),
       FOREIGN KEY (case_number) REFERENCES Cases(case_number),
       FOREIGN KEY (tube_type_instance) REFERENCES TubeTypesInstances(tube_type_instance)
);
CREATE INDEX IF NOT EXISTS ix_TubeCases_case_number
       ON TubeCases (case_number);
CREATE INDEX IF NOT EXISTS ix_TubeCases_date_cytnum
       ON TubeCases (date, cytnum);
CREATE UNIQUE INDEX IF NOT EXISTS ix_TubeCases_file
       ON TubeCases (filename, dirname);
CREATE INDEX IF NOT EXISTS ix_TubeCases_tube_type_instance
       ON TubeCases (tube_type_instance);

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
       case_tube_idx INTEGER NOT NULL,
      "Channel Number" INTEGER NOT NULL,
       count INTEGER,
       mean FLOAT,
       std FLOAT,
       min FLOAT,
       "25%" FLOAT,
       "50%" FLOAT,
       "75%" FLOAT,
       max FLOAT,
       transform_in_limits INTEGER,
       transform_not_nan INTEGER,
       version VARCHAR(30) NOT NULL,
       PRIMARY KEY (case_tube_idx, "Channel Number"),
       FOREIGN KEY (case_tube_idx) REFERENCES TubeCases(case_tube_idx)
);

CREATE INDEX IF NOT EXISTS ix_PmtStats_Channel_Number
       ON PmtStats ("Channel Number");

-- Tube event stats
CREATE TABLE IF NOT EXISTS TubeStats (
       case_tube_idx NVARCHAR(100) PRIMARY KEY,
       total_events INTEGER NOT NULL,
       transform_not_nan INTEGER NOT NULL,
       transform_in_limits INTEGER NOT NULL,
       viable_remain INTEGER NULL,
       singlet_remain INTEGER NULL,
       version VARCHAR(30) NOT NULL,
       FOREIGN KEY (case_tube_idx) REFERENCES TubeCases (case_tube_idx)
);

-- Pmt event histogram
CREATE TABLE IF NOT EXISTS PmtHistos (
       case_tube_idx INTEGER NOT NULL,
       "Channel Number" NVARCHAR(5) NOT NULL,
       bin NVARCHAR(20) NOT NULL,
       density FLOAT,
       PRIMARY KEY (case_tube_idx, "Channel Number", bin),
       FOREIGN KEY (case_tube_idx) REFERENCES TubeCases(case_tube_idx)
);
CREATE INDEX IF NOT EXISTS PmtHistos_bin
       ON PmtHistos ("Channel Number", bin);
