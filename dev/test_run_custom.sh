#!/usr/bin/env bash
#
# Wrapper for MLanalysis usng custom data built off of already existing meta_data, custom data file, and FCS data folder
#
# Example: ~/repos/flow_anal/dev/test_run_custom.sh /home/local/AMC/ngdavid/clinical_cHL_cases/ ~/repos/flow_anal/db/Hodgkins/fcs.db ~/working/Hodgkin/test_cases.txt

# INPUT
dir=$1 # Directory to crawl
metadb=$2 # Build of meta database
custom_data=$3 # Custom data text file
q_options="${@:4}"

# OUTPUT files
wdir=`pwd`
feature_hdf5file=$wdir/fcs_features.hdf5
ML_input_hdf5file=$wdir/ML_input.hdf5
custom_annot=$wdir/annots.txt
rm $feature_hdf5file
rm $ML_input_hdf5file
rm $custom_annot

# ENTRY python script
script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
FLOWANAL=$script_dir/..

python $FLOWANAL/setup.py -h >> /dev/null

echo -e "\n################# Make features from data #########"
cmd="$FLOWANAL/flowanal.py -v make_features $1
  -db $2
  --feature-hdf5 $feature_hdf5file
  $q_options
"
echo $cmd
#$cmd

echo -e "\n################# Make clinical data #########"
cmd="cp $3 $custom_annot"
echo $cmd
$cmd

echo -e "\n################# Make data for ML #########"
cmd="$FLOWANAL/flowanal.py -vv make_ML_input
  -db $2
  --feature-hdf5 $feature_hdf5file
  -annot $custom_annot
  -ml-hdf5 $ML_input_hdf5file"
echo $cmd
$cmd
