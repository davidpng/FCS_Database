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
dbfile=$wdir/fcs_custom_test.db
hdf5file=$wdir/fcs_features.hdf5
rm $dbfile
rm $hdf5file

# ENTRY python script
script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
FLOWANAL=$script_dir/..

python $FLOWANAL/setup.py -h >> /dev/null

echo -e "\n################# Add custom data #################"
$FLOWANAL/flowanal.py -v add_CustomCaseData_db $3 -db $2 -outdb $dbfile
# outdb should only include cases in the metadb and the custom cases

echo -e "\n################# Make features from data #########"
$FLOWANAL/flowanal.py -v make_features $1 -db $dbfile -hdf5 $hdf5file
# if feature_extraction fails
# 1. will not include in HDF5 
# 2. added case (via case_tube_idx) to exclude list and flag reason why
# 3. Remove case from dbfile

echo -e "\n################# pick correct case_tube_idx #########"
#this will be a dbfile search that deletes a subset of case_tube_idx that are repeated
#due to repeat processes (pick most recent rpt file)


echo -e "\n################# Merge features #########"
#$FLOWANAL/flowanal.py -v run_ML_on_TubeCases -db $dbfile -hdf5 $hdf5file
# build checks to make sure HDF5 has case_tube_idx that is being query.
