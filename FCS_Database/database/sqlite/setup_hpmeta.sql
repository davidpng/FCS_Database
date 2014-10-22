-- Create tables and constraints for hematopathology flow cytometry
-- meta information
-- index name convention is ix_<table>_<column1>[_<column2>...]

--PRAGMA foreign_keys = ON;

-- Exp_Tube_Pmt
CREATE TABLE IF NOT EXISTS PmtTubeExp (
       Filename NVARCHAR(100) NOT NULL,
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
       PRIMARY KEY (Filename, Antigen, Fluorophore)
       FOREIGN KEY (Filename) REFERENCES TubeExp(Filename),
       FOREIGN KEY (Antigen) REFERENCES Antigens(Antigen),
       FOREIGN KEY (Fluorophore) REFERENCES Fluorophores(Fluorophore)
);
CREATE INDEX IF NOT EXISTS ix_PmtTubeExp_antigen
       ON PmtTubeExp (Antigen);
CREATE INDEX IF NOT EXISTS ix_PmtTubeExp_antigen_fluor
       ON PmtTubeExp (Antigen, Fluorophore);
CREATE INDEX IF NOT EXISTS ix_PmtTubeExp_number
       ON PmtTubeExp ("Channel Number");
CREATE INDEX IF NOT EXISTS ix_PmtTubeExp_antigen_number
       ON PmtTubeExp (Antigen, "Channel Number");

-- Tube experiment
CREATE TABLE IF NOT EXISTS TubeExp (
       Filename NVARCHAR(100) PRIMARY KEY,
       dirname NVARCHAR(255) NOT NULL,
       case_id NVARCHAR(10) NOT NULL,
       tube_type_instance NVARCHAR(20),
       date DATETIME NOT NULL,
       num_events INTEGER,
       cytometer NVARCHAR(10),
       cytnum INTEGER,
       FOREIGN KEY (case_id) REFERENCES Exp(case_id),
       FOREIGN KEY (tube_type_instance) REFERENCES TubeTypeInstances(tube_type_instance)
);
CREATE INDEX IF NOT EXISTS ix_TubeExp_case_id
       ON TubeExp (case_id);
CREATE INDEX IF NOT EXISTS ix_TubeExp_date
       ON TubeExp (date);

-- Experiments
CREATE TABLE IF NOT EXISTS Exp (
       case_id NVARCHAR(10) PRIMARY KEY,
       MRN NVARCHAR(20)
);

-- Tube types
CREATE TABLE IF NOT EXISTS TubeTypesInstances (
       tube_type_instance NVARCHAR(20) PRIMARY KEY,
       tube_type NVARCHAR(20) NOT NULL,
       Antigen NVARCHAR(10) NOT NULL,
       FOREIGN KEY (tube_type) REFERENCES TubeTypes (tube_type),
       FOREIGN KEY (Antigen) REFERENCES Antigens(Antigen)
);
CREATE INDEX IF NOT EXISTS ix_TubeTypeInstances_tube_type
       ON TubeTypesInstances(tube_type);
CREATE INDEX IF NOT EXISTS ix_TubeTypeInstances_antigen
       ON TubeTypesInstances(Antigen);
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
