#!/usr/bin/env python3

import argparse
import atexit
import serial
from serial.serialposix import Serial
import serial.tools.list_ports
import struct
import time

from datetime import datetime

from mixer import Mode
from uart_wrapper import SerialInCommands, SerialOutCodes

DEFAULT_BAUD=115200

def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--device', type=str)
    parser.add_argument('-b', '--baudrate', default=DEFAULT_BAUD, type=int)
    parser.add_argument('-l', '--bitlen', type=int)
    parser.add_argument('-m', '--monitor', action='store_true')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('-p', '--pps', action='store_true')
    inv = parser.add_mutually_exclusive_group()
    inv.add_argument('-i', '--invert-first-code', action='store_true')
    inv.add_argument('-I', '--no-invert-first-code', action='store_true')
    parser.add_argument('-ta', '--taps-a', type=int)
    parser.add_argument('-tb', '--taps-b', type=int)
    parser.add_argument('-M', '--mode', choices=Mode._member_names_)
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

    s = serial.Serial(args.device, args.baudrate, bytesize=8, parity=serial.PARITY_EVEN)
    atexit.register(s.close)

    if args.mode:
        match Mode[args.mode]:
            case Mode.CARRIER:
                s.write(SerialInCommands.MODE_CARRIER.value.to_bytes())
            case Mode.BPSK:
                s.write(SerialInCommands.MODE_BPSK.value.to_bytes())
            case Mode.QPSK:
                s.write(SerialInCommands.MODE_QPSK.value.to_bytes())
        s.flush()

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
                    if args.pps:
                        print("PPS")
                case SerialOutCodes.PPS_EARLY:
                    print("PPS EARLY")
                case SerialOutCodes.PPS_LATE:
                    print("PPS LATE")
                case SerialOutCodes.SERIAL_RX_OVERFLOW_ERROR:
                    print("SERIAL OVERFLOW")
                case SerialOutCodes.SERIAL_RX_FRAME_ERROR:
                    print("SERIAL FRAME ERROR")
                case SerialOutCodes.SERIAL_RX_PARITY_ERROR:
                    print("SERIAL PARITY ERROR")
                case SerialOutCodes.UNKNOWN_COMMAND_ERROR:
                    print("UNKNOWN COMMAND ERROR")
                case _:
                    print(f"Error : unhandled code {code}")

if __name__ == '__main__':
    main()
