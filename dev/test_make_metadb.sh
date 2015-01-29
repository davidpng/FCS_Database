#!/usr/bin/env bash
#
# Wrapper for building meta database
#
# Example: ~/repos/flow_anal/dev/test_make_metadb.sh /home/local/AMC/ngdavid/clinical_cHL_cases/

dir=$1 # Directory to crawl
n=$2 # Number of files

# OUTPUT files
wdir=`pwd`
file_list=$wdir/fcs_file_list.txt
dbfile=$wdir/fcs_meta.db
rm $dbfile

# ENTRY python script
script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
FLOWANAL=$script_dir/..

python $FLOWANAL/setup.py -h >> /dev/null

echo -e "\n############# Make file list ############"
cmd="$FLOWANAL/flowanal.py -v make_FCS_file_list $dir -o $file_list"

if [ ! -z "$n" ]; then
cmd="$cmd -n $n"
fi
echo $cmd
$cmd

echo -e "\n################ Make meta db ##########"
cmd="$FLOWANAL/flowanal.py -v make_FCSmeta_db $dir -fl $file_list -db $dbfile"
echo $cmd
$cmd

echo -e "\n################# TEST QUERY DB #################"
cmd="$FLOWANAL/flowanal.py -v query_db --getTubeInfo -etype df -db $dbfile"
echo $cmd
$cmd
