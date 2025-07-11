#!/bin/bash

rep='/data/'

pid=`ps aux | grep multi_ | grep -v grep | cut -d\  -f2`; if [[ -n "$pid" ]]; then echo "killed $pid";kill -9 $pid;fi
sleep 30
echo "Start"
ladate=`date +%s`
touch ${rep}/file2.bin
while (test $( ls -s  ${rep}/file2.bin | cut -d\  -f1 ) -le 10) do # repeat measurement until success
  nice -n -20 /home/jmfriedt/2401/rx_multi_samples > ${rep}/$ladate.log 2>&1 &
  # /usr/bin/python3 /home/jmfriedt/2401/acq5min.py > ${rep}/$ladate.log 2>&1 &
  echo "Waiting"
  wait
done
echo "Finished"
ladatefin=`date +%s`
fractionfin=`stat -c "%y" ${rep}/file1.bin  | cut -d\.  -f2 | cut -d\  -f1`
entierfin=`stat -c "%Y" ${rep}/file1.bin`
echo "${ladate}_${entierfin}.${fractionfin}"
mv ${rep}/file1.bin ${rep}/${ladate}_${entierfin}.${fractionfin}_1.bin
fractionfin=`stat -c "%y" ${rep}/file2.bin  | cut -d\.  -f2 | cut -d\  -f1`
entierfin=`stat -c "%Y" ${rep}/file2.bin`
echo "${ladate}_${entierfin}.${fractionfin}"
mv ${rep}/file2.bin ${rep}/${ladate}_${entierfin}.${fractionfin}_2.bin
uhd_usrp_probe # reset RFNOC ?
