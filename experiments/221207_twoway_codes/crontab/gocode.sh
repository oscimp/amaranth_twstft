ENA=18   # first pin after communication    o oTX
DIR=27   # opposite to GND after GPIO18  GNDo oRX
         #                                  o o18
         #                                27o oGND

if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
  else
    bitstream=`ls /root/bitstreams/*bit | head -$1 | tail -1`
    echo $1 $bitstream
    openFPGALoader -b zedboard --freq 30e6 -m $bitstream

# listeprocess=`ps aux | grep pyth | grep -v grep`                              
echo $listeprocess
# if [ -z "$listeprocess" ]; then 
#    echo "lancement" 
#    python3 /root/b210_continuous_interleaved.py & 
# fi

if [ ! -e /sys/class/gpio/gpio$DIR ]; then 
  echo "$DIR" >  /sys/class/gpio/export
  echo "out" >  /sys/class/gpio/gpio$DIR/direction
  echo "1" >  /sys/class/gpio/gpio$DIR/value
fi
if [ ! -e /sys/class/gpio/gpio$ENA ]; then 
  echo "$ENA" >  /sys/class/gpio/export
  echo "out" >  /sys/class/gpio/gpio$ENA/direction
  echo "0" >  /sys/class/gpio/gpio$ENA/value
fi

ladate=`date +%s`
echo "Start"
/usr/bin/python3 /root/b210_file.py &> /tmp/$ladate.log &
sleep 10  # attend que la B210 se lance
echo "Emitting"
echo "out" >  /sys/class/gpio/gpio$ENA/direction
echo "out" >  /sys/class/gpio/gpio$DIR/direction
echo "1" >  /sys/class/gpio/gpio$ENA/value
echo "0" >  /sys/class/gpio/gpio$DIR/value
echo "Waiting"
wait
echo "Finished"
ladatefin=`date +%s`
echo "0" >  /sys/class/gpio/gpio$ENA/value  # switch off FPGA
echo "1" >  /sys/class/gpio/gpio$DIR/value  # switch to 50 ohm load
mv /tmp/fichier.bin /root/data/$ladate.bin
mv /tmp/$ladate.log /root/data
touch /root/data/$ladatefin
fi
