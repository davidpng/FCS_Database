FCS_Database
============

Program to analyze flow cytometry .fcs files


DEV setup
============
dev/venv.sh

Load HP database meta information (example)
==========
FCS_Database-env/bin/activate

# Make FCS db
./flowanal.py make_FCSmeta_db --dir /home/local/AMC/ngdavid/clinical_cHL_cases/

# Export Tube types data
./flowanal.py tube_types -export

# Import Tube types data
<edit> db/tube_types.tmp
./flowanal.py tube_types -load

# Query FCS db for Hodgkins tubes
./flowanal.py query_db --tubes Hodgkins --exporttype df --outfile db/tubetypes.tmp

# Update package version
python setup.py -h
