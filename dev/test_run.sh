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

./flowanal.py -v process_FCSstats --table-format tall --testing

echo -e "\n################# MAKE PICTURES #################"
./flowanal.py -v viz-cases-2d $dir -n 1

echo -e "\n################# QUERY DB #################"
./flowanal.py -v query_db --getTubeInfo -etype df -o db/test.txt

echo -e "\n################# Extract features ############"
./flowanal.py -v make_features $dir

echo -e "\n################# Read features to Memory ##########"
./flowanal.py -v query_merge_features
