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

echo -e "\n################# Make features from data #########"
$FLOWANAL/flowanal.py -v make_features $1 -db $dbfile -hdf5 $hdf5file

echo -e "\n################# Merge features #########"
#$FLOWANAL/flowanal.py -v run_ML_on_TubeCases -db $dbfile -hdf5 $hdf5file
