#!/usr/bin/env bash
#
# Make QC data from fcs_stats.db
#
# Example: ~/repos/flow_anal/dev/test_make_qc.sh /home/local/AMC/ngdavid/workspace/FCS_Full/fcs_stats_full.db

# INPUT
stats_db=$1 # Build of stats database
q_options="${@:4}"

# OUTPUT files
wdir=`pwd`
qc_db=$wdir/fcs_qc.db

# ENTRY python script
script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
FLOWANAL=$script_dir/..

python $FLOWANAL/setup.py -h >> /dev/null

echo -e "\n################# Gather and push stats into df #########"
rm $qc_db
cmd="$FLOWANAL/flowanal.py -v process_FCSstats --db $stats_db
 --outdb $qc_db
  --testing
  $q_options
"
echo "CMD: $cmd"
$cmd
