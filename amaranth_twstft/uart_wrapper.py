#!/usr/bin/env python3

from enum import Enum
from amaranth import *
from amaranth.lib.wiring import Component, In, Out
from amaranth_stdio.serial import AsyncSerial, Parity

from mixer import Mode

class SerialInCommands(Enum):
    SET_INVERT_FIRST_CODE = 0
    UNSET_INVERT_FIRST_CODE = 1
    SET_TAPS_A = 2
    SET_TAPS_B = 3
    MODE_CARRIER = 4
    MODE_BPSK = 5
    MODE_QPSK = 6

class SerialOutCodes(Enum):
    NOTHING = 0
    PPS_GOOD = 1
    PPS_EARLY = 2
    PPS_LATE = 3
    SERIAL_RX_OVERFLOW_ERROR = 4
    SERIAL_RX_FRAME_ERROR = 5
    SERIAL_RX_PARITY_ERROR = 6
    UNKNOWN_COMMAND_ERROR = 7

class UARTWrapper(Component):
    mode: Out(Shape.cast(Mode))

    # flags
    pps_good: In(1)
    pps_early: In(1)
    pps_late: In(1)

    def __init__(self, clk_freq, bitlen, pins):
        super().__init__()
        self.clk_freq = clk_freq
        self.bitlen = bitlen
        self.pins = pins

    def elaborate(self, platform):
        m = Module()

        m.submodules.uart = uart = AsyncSerial(
                divisor=int(self.clk_freq // 115200),
                data_bits=8,
                parity=Parity.EVEN,
                pins=self.pins)

        # raise external flags
        pps_good_flag = Signal()
        with m.If(self.pps_good):
            m.d.sync += pps_good_flag.eq(True)
        pps_late_flag = Signal()
        with m.If(self.pps_late):
            m.d.sync += pps_late_flag.eq(True)
        pps_early_flag = Signal()
        with m.If(self.pps_early):
            m.d.sync += pps_early_flag.eq(True)

        # internal flags
        unknown_command_flag = Signal()
        rx_overflow_flag = Signal()
        with m.If(uart.rx.err.overflow):
            m.d.sync += rx_overflow_flag.eq(True)
        rx_frame_flag = Signal()
        with m.If(uart.rx.err.frame):
            m.d.sync += rx_frame_flag.eq(True)
        rx_parity_flag = Signal()
        with m.If(uart.rx.err.parity):
            m.d.sync += rx_parity_flag.eq(True)

        with m.FSM(reset="WAITING"):
            with m.State("WAITING"):
                m.d.comb += uart.rx.ack.eq(True)
                with m.If(uart.rx.rdy):
                    with m.Switch(uart.rx.data):
                        with m.Case(SerialInCommands.MODE_CARRIER):
                            m.d.sync += self.mode.eq(Mode.CARRIER)
                        with m.Case(SerialInCommands.MODE_BPSK):
                            m.d.sync += self.mode.eq(Mode.BPSK)
                        with m.Case(SerialInCommands.MODE_QPSK):
                            m.d.sync += self.mode.eq(Mode.QPSK)
                        with m.Default():
                            m.d.sync += unknown_command_flag.eq(True)
                with m.Elif(uart.tx.rdy):
                    def if_flag_send(flag: Signal, code: int, reset: bool = True, is_elif=False):
                        with m.Elif(flag) if is_elif else m.If(flag):
                            m.d.comb += [
                                uart.tx.ack.eq(True),
                                uart.tx.data.eq(code),
                            ]
                            if reset: # lower the flag
                                m.d.sync += flag.eq(False)
                            m.next = "SET_TX_TO_ZERO"
                    def elif_flag_send(flag: Signal, code: int, reset: bool = True):
                        if_flag_send(flag, code, reset, True)

                    if_flag_send(unknown_command_flag, SerialOutCodes.UNKNOWN_COMMAND_ERROR)
                    elif_flag_send(pps_good_flag, SerialOutCodes.PPS_GOOD)
                    elif_flag_send(pps_late_flag, SerialOutCodes.PPS_LATE)
                    elif_flag_send(pps_early_flag, SerialOutCodes.PPS_EARLY)
                    elif_flag_send(rx_overflow_flag, SerialOutCodes.SERIAL_RX_OVERFLOW_ERROR)
                    elif_flag_send(rx_frame_flag, SerialOutCodes.SERIAL_RX_FRAME_ERROR)
                    elif_flag_send(rx_parity_flag, SerialOutCodes.SERIAL_RX_PARITY_ERROR)
            with m.State("SET_TX_TO_ZERO"):
                with m.If(uart.tx.rdy):
                    m.d.comb += [
                        uart.tx.ack.eq(True),
                        uart.tx.data.eq(SerialOutCodes.NOTHING),
                    ]
                    m.next = "WAITING"
        return m
