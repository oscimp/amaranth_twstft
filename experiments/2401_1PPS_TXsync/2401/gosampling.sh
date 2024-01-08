#!/bin/bash
sleep 40
ladate=`date +%s`
echo "Start"
/usr/bin/python3 /home/jmfriedt/2401/acq5min.py > /data/$ladate.log 2>&1 &
sleep 15  # attend que la X310 se lance
ladatedeb=`date +%s`
echo "Waiting"
wait
echo "Finished"
ladatefin=`date +%s`
fractionfin=`stat -c "%y" /data/fichier.bin  | cut -d\.  -f2 | cut -d\  -f1`
entierfin=`stat -c "%Y" /data/fichier.bin`
echo "${ladate}_${entierfin}.${fractionfin}"
mv /data/fichier.bin /data/${ladate}_${entierfin}.${fractionfin}.bin
