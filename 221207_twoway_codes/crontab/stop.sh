ENA=18   # first pin after communication    o oTX
DIR=27   # opposite to GND after GPIO18  GNDo oRX
         #                                  o o18
         #                                27o oGND

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

echo "0" >  /sys/class/gpio/gpio$ENA/value  # switch off FPGA
echo "1" >  /sys/class/gpio/gpio$DIR/value  # switch to 50 ohm load
