#!/usr/bin/env python3
import twstft_config

# start @ 4:00 and 46:00
# ends  @ 9:00 and 51:00

import time
import threading
from datetime import datetime
s=twstft_config.new_serial("/dev/ttyUSB1")
twstft_config.set_calib_mode(s,twstft_config.CalibrationMode.AUTO)
print("calibrating PPS")
time.sleep(5)
twstft_config.set_calib_mode(s,twstft_config.CalibrationMode.OFF)

def processing():
   global delai, somme
   now=datetime.now()
   erreur=(now.microsecond-500000)/1000000    # stay between two 1-PPS
   delai=1.-erreur
   threading.Timer(delai, processing).start()
   current_time=now.strftime("%H:%M:%S.%f")
   print(current_time,end=" ")
   twstft_config.print_logs(s)
   print(f"{now.hour} {now.minute} {now.second}")
   if ((now.hour % 2)==1) :                           # odd hour
      if ((now.minute == 3) or (now.minute == 45)) :  # minute-1 44
         if (now.second == 59) :                      # 59"
            twstft_config.set_taps(s, 17, 15, None)  # bitlen, taps (BPSK), taps (QPSK)
            twstft_config.set_timecode_mode(s,twstft_config.TimeCoderMode.OFF)
            twstft_config.set_calib_mode(s,twstft_config.CalibrationMode.AUTO)
            # twstft_config.set_calib_mode(s,twstft_config.CalibrationMode.OFF)
            twstft_config.set_mode(s,twstft_config.Mode.BPSK)
            print(f"{current_time}: ON")
      if ((now.minute == 9) or (now.minute == 51) or (now.minute == 36)) :  # minute   48
         if (now.second == 00) :                     # 00"
            twstft_config.set_mode(s,twstft_config.Mode.OFF)
            twstft_config.set_calib_mode(s,twstft_config.CalibrationMode.OFF)
            print(f"{current_time}: OFF")

processing()
