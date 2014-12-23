#!/usr/bin/env bash
n=$1 # Number of files

python setup.py -h >> /dev/null

rm -i db/*

./flowanal.py -v make_FCS_file_list /home/local/AMC/ngdavid/clinical_cHL_cases/ -n $n

./flowanal.py -v make_FCSmeta_db /home/local/AMC/ngdavid/clinical_cHL_cases/

./flowanal.py -v add_FCSstats_db /home/local/AMC/ngdavid/clinical_cHL_cases/ -tubes Hodgkin Hodgkins

./flowanal.py -v process_FCSstats -tubes Hodgkin Hodgkins --table-format tall --testing

