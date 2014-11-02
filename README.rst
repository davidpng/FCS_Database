FCS_Database
============

Program to scrape an FCS directory of metadata


DEV setup
============
dev/venv.sh

Load HP database meta information (example)
==========
FCS_Database-env/bin/activate

# Make FCS db
./FCS_Database/load_FCSdb.py --dir /home/local/AMC/ngdavid/clinical_cHL_cases --rebuilddb

# Export Tube types data
./FCS_Database/tube_types.py -export -file data/tube_types.tmp

# Import Tube types data
./FCS_Database/tube_types.py -load -file data/tube_types.csv

# Query FCS db for Hodgkins tubes
./FCS_Database/query_db.py -tubes Hodgkins -exporttype dict_dict

