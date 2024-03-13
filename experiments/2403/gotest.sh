#!/bin/bash
pid=`ps aux | grep zmq_rx_short | grep -v grep | cut -d\  -f2` 
if [[ -n "$pid" ]]; then 
	echo "killed ZMQ $pid" >> $HOME/2403/killed
	kill -9 $pid
fi
if [ -f "/data/test.bin" ]; then
    rm -f /data/test.bin
fi
ladate=`date`
echo "Start"
echo -n $ladate >> $HOME/2403/log
nice -n -20 /usr/bin/python3 $HOME/2403/zmq_rx_short.py &
echo "Waiting"
wait
echo "Finished"
ls -l /data/test.bin >>  $HOME/2403/log 
