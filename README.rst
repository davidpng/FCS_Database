FlowAnal
============

Program to analyze flow cytometry .fcs files


DEV setup
============
dev/venv.sh

Load HP database meta information (example)
==========
FCS_Database-env/bin/activate

# Update version
python setup.py -h

# Make FCS db
./flowanal.py make_FCSmeta_db /home/local/AMC/ngdavid/clinical_cHL_cases/

# Export Tube types data
./flowanal.py tube_types -export

# Import Tube types data
<edit> db/tube_types.tmp
./flowanal.py tube_types -load

# Query FCS db for Hodgkins tubes
./flowanal.py query_db --tubes Hodgkins --daterange 2012-01-01 2013-01-01 --outfile db/cases.tmp

# Template for querying FCS db and doing something with results
./flowanal.py template-query_do /home/local/AMC/ngdavid/clinical_cHL_cases/ -tubes Hodgkins -dates 2013-1-1 2013-1-10


