#!/usr/bin/env bash
#
# Wrapper for building meta database
#
# Example: ~/repos/flow_anal/dev/test_make_metadb.sh /home/local/AMC/ngdavid/clinical_cHL_cases/

dir=$1 # Directory to crawl
n=$2 # Number of files
file_list_input=$3 #Input file list (drive analysis off of)

# OUTPUT files
wdir=`pwd`
file_list=$wdir/fcs_file_list.txt
dbfile=$wdir/fcs_meta.db
rm $dbfile

# ENTRY python script
script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
FLOWANAL=$script_dir/..

python $FLOWANAL/setup.py -h >> /dev/null

if [ -z $file_list_input ]; then
    echo -e "\n############# Make file list ############"
    cmd="$FLOWANAL/flowanal.py -v make_FCS_file_list $dir -o $file_list"

    if [ ! -z "$n" ]; then
	cmd="$cmd -n $n"
    fi
    echo $cmd
    $cmd
else
    file_list=$file_list_input
fi

echo -e "\n################ Make meta db ##########"
cmd="$FLOWANAL/flowanal.py -v make_FCSmeta_db $dir -fl $file_list -db $dbfile"
if [ ! -z "$n" ]; then
    cmd="$cmd -n $n"
fi
echo $cmd
$cmd
