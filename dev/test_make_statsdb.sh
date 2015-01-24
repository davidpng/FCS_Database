#!/usr/bin/env bash
#
# Wrapper for building meta database
#
# Example: ~/repos/flow_anal/dev/test_make_metadb.sh /home/local/AMC/ngdavid/clinical_cHL_cases/

dir=$1 # Directory to crawl
metadb=$2  # Meta db to build off of
q_options="${@:4}"

# OUTPUT files
wdir=`pwd`

statsdb=$wdir/fcs_stats.db
rm $statsdb

# ENTRY python script
script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
FLOWANAL=$script_dir/..

python $FLOWANAL/setup.py -h >> /dev/null

echo -e "\n############# Make stats db ############"
cmd="$FLOWANAL/flowanal.py -v par_add_stats_db $dir
  -db $metadb
  -outdb $statsdb
  --testing
  $q_options"
echo $cmd
$cmd
