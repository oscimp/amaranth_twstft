#!/bin/bash
pid=`ps aux | grep multi_ | grep -v grep | cut -d\  -f2`; if [[ -n "$pid" ]]; then echo "killed $pid";kill -9 $pid;fi
sleep 30
echo "Start"
ladate=`date +%s`
touch /data/file2.bin
while (test $( ls -s  /data/file2.bin | cut -d\  -f1 ) -le 10) do # repeat measurement until success
  nice -n -20 /home/jmfriedt/2401/rx_multi_samples > /data/$ladate.log 2>&1 &
  # /usr/bin/python3 /home/jmfriedt/2401/acq5min.py > /data/$ladate.log 2>&1 &
  echo "Waiting"
  wait
done
echo "Finished"
ladatefin=`date +%s`
fractionfin=`stat -c "%y" /data/file1.bin  | cut -d\.  -f2 | cut -d\  -f1`
entierfin=`stat -c "%Y" /data/file1.bin`
echo "${ladate}_${entierfin}.${fractionfin}"
mv /data/file1.bin /data/${ladate}_${entierfin}.${fractionfin}_1.bin
fractionfin=`stat -c "%y" /data/file2.bin  | cut -d\.  -f2 | cut -d\  -f1`
entierfin=`stat -c "%Y" /data/file2.bin`
echo "${ladate}_${entierfin}.${fractionfin}"
mv /data/file2.bin /data/${ladate}_${entierfin}.${fractionfin}_2.bin
uhd_usrp_probe # reset RFNOC ?
