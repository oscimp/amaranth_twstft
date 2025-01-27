#!/usr/bin/env python3

import argparse
import atexit
from math import ceil
import serial
from serial.serialposix import Serial
import serial.tools.list_ports
import struct
import time

from datetime import datetime

from time_coder import TimeCoderMode
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
    parser.add_argument('-t', '--set-time', action='store_true')
    parser.add_argument('-T', '--time-mode', choices=TimeCoderMode._member_names_)
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

    if args.time_mode:
        match TimeCoderMode[args.time_mode]:
            case TimeCoderMode.OFF:
                s.write(SerialInCommands.TIMECODER_OFF.value.to_bytes())
            case TimeCoderMode.INVERT_FIRST_CODE:
                s.write(SerialInCommands.TIMECODER_INVERT_FIRST_CODE.value.to_bytes())
            case TimeCoderMode.TIMECODE:
                s.write(SerialInCommands.TIMECODER_TIMECODE.value.to_bytes())
        s.flush()

    set_time = False
    if args.set_time:
        set_time = True # We dont set time right away,
                        # To avoid errors, the fpga's time has to be set before the pps
                        # marking the begining of the next second.
                        # Assuming the PPS marks the true begining of the second,
                        # and that our computer is more or less in sync,
                        # we first wait for a good pps to be detected by the fpga,
                        # then half a second to account for a poorly synchronized computer,
                        # and finaly we set the fpga's time to computer's time.

    if args.taps_a:
        if not args.bitlen:
            parser.error("--bitlen must be specified when setting taps")
        s.write(struct.pack(
            '<bq',
            SerialInCommands.SET_TAPS_A.value,
            args.taps_a)[0:1+ceil(args.bitlen/s.bytesize)])
    if args.taps_b:
        if not args.bitlen:
            parser.error("--bitlen must be specified when setting taps")
        s.write(struct.pack(
            '<bq',
            SerialInCommands.SET_TAPS_B.value,
            args.taps_b)[0:1+ceil(args.bitlen/s.bytesize)])

    if args.monitor or set_time:
        while True:
            code = s.read(1)[0]
            try:
                code = SerialOutCodes(code)
            except ValueError:
                print(f"Error : unknown code {code}")
                continue
            match code:
                case SerialOutCodes.NOTHING:
                    pass
                case SerialOutCodes.PPS_GOOD:
                    if args.pps:
                        print("PPS")
                    if set_time:
                        time.sleep(0.5) # aproximate middle of the true second
                        s.write(struct.pack(
                            '<bb',
                            SerialInCommands.SET_TIME.value,
                            int(time.time())&0xff
                            ))
                        set_time = False
                        if not args.monitor:
                            exit(0)
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
                case SerialOutCodes.CODE_UNALIGNED:
                    print("CODE UNALIGNED")
                case SerialOutCodes.SYMBOL_UNALIGNED:
                    print("SYMBOL UNALIGNED")
                case SerialOutCodes.OSCIL_UNALIGNED:
                    print("OSCIL UNALIGNED")
                case _:
                    print(f"Error : unhandled code {code}")

if __name__ == '__main__':
    main()
