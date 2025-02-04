#!/usr/bin/env python3

import argparse
import atexit
from math import ceil
import sys
from typing import Callable, Coroutine, Dict, List
import serial
from serial.serialposix import Serial
import serial.tools.list_ports
import struct
import time

from datetime import datetime

from calibration_output import CalibrationMode
from time_coder import TIMECODE_SIZE, TimeCoderMode
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
    parser.add_argument('-ta', '--taps-a', type=int)
    parser.add_argument('-tb', '--taps-b', type=int)
    parser.add_argument('-t', '--set-time', action='store_true')
    parser.add_argument('-M', '--mode', choices=Mode._member_names_)
    parser.add_argument('-T', '--time-mode', choices=TimeCoderMode._member_names_)
    parser.add_argument('-C', '--calib-mode', choices=CalibrationMode._member_names_)
    return parser

def set_mode(s: serial.Serial, mode: Mode):
    match mode:
        case Mode.CARRIER:
            s.write(SerialInCommands.MODE_CARRIER.value.to_bytes())
        case Mode.BPSK:
            s.write(SerialInCommands.MODE_BPSK.value.to_bytes())
        case Mode.QPSK:
            s.write(SerialInCommands.MODE_QPSK.value.to_bytes())
    s.flush()

def set_timecode_mode(s: serial.Serial, mode: TimeCoderMode):
    match mode:
        case TimeCoderMode.OFF:
            s.write(SerialInCommands.TIMECODER_OFF.value.to_bytes())
        case TimeCoderMode.INVERT_FIRST_CODE:
            s.write(SerialInCommands.TIMECODER_INVERT_FIRST_CODE.value.to_bytes())
        case TimeCoderMode.TIMECODE:
            s.write(SerialInCommands.TIMECODER_TIMECODE.value.to_bytes())
    s.flush()

def set_calib_mode(s: serial.Serial, mode: CalibrationMode):
    match mode:
        case CalibrationMode.OFF:
            s.write(SerialInCommands.CALIB_OFF.value.to_bytes())
        case CalibrationMode.CLK:
            s.write(SerialInCommands.CALIB_CLK.value.to_bytes())
        case CalibrationMode.PPS:
            s.write(SerialInCommands.CALIB_PPS.value.to_bytes())
    s.flush()

def set_taps(s: serial.Serial, bitlen: int, taps_a:int = None, taps_b:int = None):
    if taps_a is not None:
        s.write(struct.pack(
            '<BQ',
            SerialInCommands.SET_TAPS_A.value,
            taps_a)[0:1+ceil(bitlen/s.bytesize)])
    if taps_b is not None:
        s.write(struct.pack(
            '<BQ',
            SerialInCommands.SET_TAPS_B.value,
            taps_b)[0:1+ceil(bitlen/s.bytesize)])

def set_time(s: serial.Serial, time: int):
    s.write(struct.pack(
        '<BB',
        SerialInCommands.SET_TIME.value,
        time%60))

def new_empty_monitoring_handlers():
    return {code:list() for code in SerialOutCodes.__members__.values()}

def monitor(s: serial.Serial,
            handlers: Dict[
                SerialOutCodes,
                List[Callable[[serial.Serial, SerialOutCodes], None]]]):
    while s.is_open:
        code = s.read(1)[0]
        try:
            code = SerialOutCodes(code)
        except ValueError:
            print(f"Error : unknown code {code}", file=sys.stderr)
            continue
        if code in handlers.keys():
            for handler in handlers[code]:
                handler(s, code)

def new_serial(device, baudrate=DEFAULT_BAUD):
    s = serial.Serial(device, baudrate, bytesize=8, parity=serial.PARITY_EVEN)
    atexit.register(s.close)
    return s


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

    s = new_serial(args.device, args.baudrate)

    if args.mode:
        set_mode(s, Mode[args.mode])

    if args.time_mode:
        set_timecode_mode(s, TimeCoderMode[args.time_mode])

    if args.calib_mode:
        set_calib_mode(s, CalibrationMode[args.calib_mode])

    if args.taps_a or args.taps_b:
        if not args.bitlen:
            parser.error("--bitlen must be specified when setting taps")
        set_taps(s, args.bitlen, args.taps_a, args.taps_b)

    handlers = new_empty_monitoring_handlers()
    if args.monitor:
        def print_code(_, code: SerialOutCodes):
            print(code.name)
        if args.pps:
            handlers[SerialOutCodes.PPS_GOOD].append(print_code)
        handlers[SerialOutCodes.PPS_EARLY].append(print_code)
        handlers[SerialOutCodes.PPS_LATE].append(print_code)
        handlers[SerialOutCodes.SERIAL_RX_FRAME_ERROR].append(print_code)
        handlers[SerialOutCodes.SERIAL_RX_OVERFLOW_ERROR].append(print_code)
        handlers[SerialOutCodes.SERIAL_RX_PARITY_ERROR].append(print_code)
        handlers[SerialOutCodes.CODE_UNALIGNED].append(print_code)
        handlers[SerialOutCodes.SYMBOL_UNALIGNED].append(print_code)
        handlers[SerialOutCodes.OSCIL_UNALIGNED].append(print_code)

    if args.set_time:
        # We dont set time right away,
        # To avoid errors, the fpga's time has to be set before the pps
        # marking the begining of the next second.
        # Assuming the PPS marks the true begining of the second,
        # and that our computer is more or less in sync,
        # we first wait for a good pps to be detected by the fpga,
        # then half a second to account for a poorly synchronized computer,
        # and finaly we set the fpga's time to computer's time.
        def set_time_handler(s: serial.Serial, _):
            time.sleep(0.4)
            set_time(s, int(time.time()))
            if not args.monitor:
                s.close()
        handlers[SerialOutCodes.PPS_GOOD].append(set_time_handler)


    if args.monitor or args.set_time:
        monitor(s, handlers)


if __name__ == '__main__':
    main()
