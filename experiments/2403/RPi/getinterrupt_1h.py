#!/usr/bin/env python3
import subprocess

# start @ 3:00 and 45:00
# ends  @ 7:00 and 49:00

def cbf(gpio, level, tick):
#   print(gpio, level, tick)
   time.sleep(0.001)
   now=datetime.now()
   current_time=now.strftime("%H:%M:%S.%f")
   print(current_time)
#   print(f"{now.hour} {now.minute} {now.second}")
   if ((now.hour % 2)==1) :                           # odd hour
#      if ((now.minute == 5) or (now.minute == 25) or (now.minute == 45)) :  # minute-1 44
      if ((now.minute == 0)) :  # minute-1 00
         if (now.second == 59) :                      # 59"
            subprocess.call("/root/2401/switch_on")
            print(f"{current_time}: ON")
#      if ((now.minute == 11) or (now.minute == 31) or (now.minute == 51)) :  # minute   48
      if ((now.minute == 59)) :  # minute   59
         if (now.second == 00) :                     # 00"
            subprocess.call("/root/2401/switch_off")
            print(f"{current_time}: OFF")

import pigpio, time
from datetime import datetime

pi=pigpio.pi()
cb1 = pi.callback(21, 1, cbf)
while (True):
	time.sleep(0.0001)
