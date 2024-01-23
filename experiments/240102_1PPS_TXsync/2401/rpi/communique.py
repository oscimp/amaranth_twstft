#!/usr/bin/env python3

import argparse
import serial
import struct
import time

from datetime import datetime

device="/dev/ttyUSB1"
baud=9600
serial = serial.Serial(device, baud)

message = serial.read(1)
mess = struct.unpack('B', message)[0]
i = int(time.time() % 60)
serial.write(struct.pack('B', i))
mess = struct.unpack('B', message)[0]
print(f"{mess} {i}")

