#!/bin/bash
pid=`ps aux | grep zmq_rx_short | grep -v grep | cut -d\  -f2` 
if [[ -n "$pid" ]]; then 
	echo "killed ZMQ $pid" >> /home/jmfriedt/2403/killed
	kill -9 $pid
fi
pid=`ps aux | grep x310 | grep -v grep | cut -d\  -f2` 
if [[ -n "$pid" ]]; then 
	echo "killed X310 $pid" >> /home/jmfriedt/2403/killed
	kill -9 $pid
fi
if [ -f "/data/test.bin" ]; then
    rm -f /data/test.bin
fi
ladate=`date`
echo "Start"
echo -n $ladate >> /home/jmfriedt/2403/log
nice -n -20 /usr/bin/python3 /home/jmfriedt/2403/zmq_rx_short.py &
echo "Waiting"
wait
echo "Finished"
ls -l /data/test.bin >>  /home/jmfriedt/2403/log 
