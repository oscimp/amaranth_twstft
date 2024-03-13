#!/bin/bash
pid=`ps aux | grep zmq | grep -v grep | cut -d\  -f2` 
if [[ -n "$pid" ]]; then 
	echo "killed ZMQ $pid" >> $HOME/2403/killed
	kill -9 $pid
fi
sleep 55
echo "Start"
ladate=`date +%s`
nice -n -20 /usr/bin/python3 $HOME/2403/acq5min.py > /data/$ladate.log 2>&1 &
echo "Waiting"
wait
echo "Finished"
ladatefin=`date +%s`
fractionfin=`stat -c "%y" /data/fichier.bin  | cut -d\.  -f2 | cut -d\  -f1`
entierfin=`stat -c "%Y" /data/fichier.bin`
echo "${ladate}_${entierfin}.${fractionfin}"
mv /data/fichier.bin /data/${ladate}_${entierfin}.${fractionfin}.bin
