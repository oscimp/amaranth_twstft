#!/usr/bin/env python3
import twstft_config

# import subprocess

# start @ 4:00 and 46:00
# ends  @ 9:00 and 51:00

s=twstft_config.new_serial("/dev/ttyUSB1")
twstft_config.set_calib_mode(s,twstft_config.CalibrationMode.OFF)

def cbf(gpio, level, tick):
#   print(gpio, level, tick)
   global s
   time.sleep(0.1)
   now=datetime.now()
   current_time=now.strftime("%H:%M:%S.%f")
   print(current_time,end=" ")
   twstft_config.print_logs(s)
#   print(f"{now.hour} {now.minute} {now.second}")
   if ((now.hour % 2)==1) :                           # odd hour
#      if ((now.minute == 5) or (now.minute == 25) or (now.minute == 45)) :  # minute-1 44
      if ((now.minute == 3) or (now.minute == 45)) :  # minute-1 44
         if (now.second == 59) :                      # 59"
#           subprocess.call("/root/2401/switch_on")
#            s=twstft_config.new_serial("/dev/ttyUSB1")
            twstft_config.set_taps(s, 17, 9, None)  # bitlen, taps (BPSK), taps (QPSK)
            twstft_config.set_timecode_mode(s,twstft_config.TimeCoderMode.OFF)
            # twstft_config.set_calib_mode(s,twstft_config.CalibrationMode.AUTO)
            twstft_config.set_calib_mode(s,twstft_config.CalibrationMode.OFF)
            twstft_config.set_mode(s,twstft_config.Mode.BPSK)
            print(f"{current_time}: ON")
#            s.close()
#      if ((now.minute == 11) or (now.minute == 31) or (now.minute == 51)) :  # minute   48
      if ((now.minute == 9) or (now.minute == 51)) :  # minute   48
         if (now.second == 00) :                     # 00"
#           subprocess.call("/root/2401/switch_off")
#            s=twstft_config.new_serial("/dev/ttyUSB1")
            twstft_config.set_mode(s,twstft_config.Mode.OFF)
            twstft_config.set_calib_mode(s,twstft_config.CalibrationMode.OFF)
            print(f"{current_time}: OFF")
#            s.close()

import pigpio, time
from datetime import datetime

pi=pigpio.pi()
cb1 = pi.callback(21, 1, cbf)
while (True):
        time.sleep(0.0001)
