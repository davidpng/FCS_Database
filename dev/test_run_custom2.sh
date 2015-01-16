#!/usr/bin/env bash
#
# Wrapper for MLanalysis usng custom data built off of already existing meta_data, custom data file, and FCS data folder
#
# Example: ~/repos/flow_anal/dev/test_run_custom.sh /home/local/AMC/ngdavid/clinical_cHL_cases/ ~/repos/flow_anal/db/Hodgkins/fcs.db ~/working/Hodgkin/test_cases.txt

# INPUT
dir=$1 # Directory to crawl
metadb=$2 # Build of meta database
custom_data=$3 # Custom data text file

# OUTPUT files
wdir=`pwd`
project_dbfile=$wdir/project.db
hdf5file=$wdir/fcs_features.hdf5
rm $dbfile
rm $hdf5file

# ENTRY python script
script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
FLOWANAL=$script_dir/..

python $FLOWANAL/setup.py -h >> /dev/null

echo -e "\n################# Query +/- whittle #################"
# copy meta_db ($2) to outdb
# if flagged (--whittle) run query and whittle out cases not found (outside scope of experiment)
#  $FLOWANAL/flowanal.py -v build_Project_db -db $2 -outdb $project_dbfile

echo -e "\n################# Add custom data #################"
$FLOWANAL/flowanal.py -v add_CustomCaseData_db $3 -db $project_dbfile [--no-whittle]
# Just add table, cases in CustomCaseData but not in dbfile get added with a comment
# outdb TubeCases.flag will be 'GOOD' if nothing has failed

## NEED to version control the database here

echo -e "\n################# Make features from data #########"
$FLOWANAL/flowanal.py -v make_features $1 -db $dbfile -hdf5 $hdf5file
# if feature_extraction fails
# 1. will not include in HDF5
# 2. Flag TubeCases.flag = failed feature extraction

# I want dbfile and hdf5file to be separable
# Need to be able to query hdf5file and get list of case_tube_idx's
# Don't store feature_failures in db


echo -e "\n################# Make features and annotations #########"
#$FLOWANAL/flowanal.py -v run_ML_on_TubeCases -db $dbfile -hdf5 $hdf5file
# build checks to make sure HDF5 has case_tube_idx that is being query.
# Make table of features and table of annotations

# Build logic in that will select most recent run of tube_type [as default option]
