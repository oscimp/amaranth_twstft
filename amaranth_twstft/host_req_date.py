#!/usr/bin/env python3

import argparse
import atexit
import serial
import serial.tools.list_ports
import struct
import time

from datetime import datetime

from uart_wrapper import SerialOutCodes

DEFAULT_BAUD=200

def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--device', type=str)
    parser.add_argument('-b', '--baudrate', default=DEFAULT_BAUD, type=int)
    parser.add_argument('-l', '--bitlen', type=int)
    parser.add_argument('-m', '--monitor', action='store_true')
    parser.add_argument('--list', action='store_true')
    inv = parser.add_mutually_exclusive_group()
    inv.add_argument('-i', '--invert-first-code', action='store_true')
    inv.add_argument('-I', '--no-invert-first-code', action='store_true')
    parser.add_argument('-ta', '--taps-a', type=int)
    parser.add_argument('-tb', '--taps-b', type=int)
    return parser

def main():
    parser = arg_parser()
    args = parser.parse_args()

    if args.list or not args.device:
        print('Serial ports :')
        print(*serial.tools.list_ports.comports(), sep='\n')
    if not args.device:
        if args.list:
            exit(0)
        else:
            parser.error("--device must be specified unless --list is")

    s = serial.Serial(args.device, args.baudrate, bytesize=8)
    atexit.register(s.close)

    if args.monitor:
        while True:
            code = s.read(1)[0]
            try:
                code = SerialOutCodes(code)
            except ValueError:
                print(f"Error : unknown code {code}")
                continue
            finally:
                s.reset_input_buffer()
            match code:
                case SerialOutCodes.NOTHING:
                    pass
                case SerialOutCodes.PPS_GOOD:
                    print("PPS")
                case _:
                    print(f"Error : unhandled code {code}")

if __name__ == '__main__':
    main()
