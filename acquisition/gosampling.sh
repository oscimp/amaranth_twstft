#!/bin/bash

acq_rep=${processing_dir:='/data/'}  # assign if processing_dir is defined, default otherwise
sto_rep=${storage_dir:='/data/'}  # assign if processing_dir is defined, default otherwise
exec_dir=${exec_dir:='/home/jmfriedt/2401/'}  # assign if processing_dir is defined, default otherwise

pid=`ps aux | grep multi_ | grep -v grep | cut -d\  -f2`; if [[ -n "$pid" ]]; then echo "killed $pid";kill -9 $pid;fi
sleep 30
uhd_usrp_probe # reset RFNOC ?
echo "Start"
ladate=`date +%s`
touch ${acq_rep}/file2.bin
while (test $( ls -s  ${acq_rep}/file2.bin | cut -d\  -f1 ) -le 10) do # repeat measurement until success
  nice -n -20 $exec_dir/rx_multi_samples --dir ${acq_rep} > ${acq_rep}/$ladate.log 2>&1 &
  # /usr/bin/python3 /home/jmfriedt/2401/acq5min.py > ${acq_rep}/$ladate.log 2>&1 &
  echo "Waiting"
  wait
done
echo "Finished"
ladatefin=`date +%s`
fractionfin=`stat -c "%y" ${acq_rep}/file1.bin  | cut -d\.  -f2 | cut -d\  -f1`
entierfin=`stat -c "%Y" ${acq_rep}/file1.bin`
echo "${ladate}_${entierfin}.${fractionfin}"
mv ${acq_rep}/file1.bin ${sto_rep}/${ladate}_${entierfin}.${fractionfin}_1.bin
fractionfin=`stat -c "%y" ${acq_rep}/file2.bin  | cut -d\.  -f2 | cut -d\  -f1`
entierfin=`stat -c "%Y" ${acq_rep}/file2.bin`
echo "${ladate}_${entierfin}.${fractionfin}"
mv ${acq_rep}/file2.bin ${sto_rep}/${ladate}_${entierfin}.${fractionfin}_2.bin
uhd_usrp_probe # reset RFNOC ?
