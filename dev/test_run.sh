#!/usr/bin/env bash
dir=$1 # Directory to crawl
n=$2 # Number of files

python setup.py -h >> /dev/null

rm -i db/*

if [ ! -z "$n" ]; then
./flowanal.py -v make_FCS_file_list $dir -n $n
else
./flowanal.py -v make_FCS_file_list $dir
fi

./flowanal.py -v make_FCSmeta_db $dir

echo -e "\n################# MAKE STATS #################"
./flowanal.py -v add_FCSstats_db $dir

#./flowanal.py -v process_FCSstats -tubes Hodgkin Hodgkins --table-format tall --testing

