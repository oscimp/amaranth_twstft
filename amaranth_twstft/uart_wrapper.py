#!/usr/bin/env python3

from enum import Enum
from amaranth import *
from amaranth.lib.wiring import Component, In, Out
from amaranth_stdio.serial import AsyncSerial

class SerialInCommands(Enum):
    SET_INVERT_FIRST_CODE = 0
    UNSET_INVERT_FIRST_CODE = 1
    SET_TAPS_A = 2
    SET_TAPS_B = 3

class SerialOutCodes(Enum):
    NOTHING = 0
    PPS_GOOD = 1
    PPS_EARLY = 2
    PPS_LATE = 3

class UARTWrapper(Component):
    # flags
    pps_good: In(1)
    pps_early: In(1)
    pps_late: In(1)

    tx_out: Out(1)

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
                pins=self.pins)

        rdy_old   = Signal()
        m.d.sync += rdy_old.eq(uart.rx.rdy)
        uart_rdy  = (~rdy_old & uart.rx.rdy)

        m.d.sync += [
            uart.rx.ack.eq(False),
        ]
        m.d.comb += self.tx_out.eq(uart.tx.o)

        pps_good_flag = Signal()
        with m.If(self.pps_good):
            m.d.sync += pps_good_flag.eq(True)
        pps_late_flag = Signal()
        with m.If(self.pps_late):
            m.d.sync += pps_late_flag.eq(True)
        pps_early_flag = Signal()
        with m.If(self.pps_early):
            m.d.sync += pps_early_flag.eq(True)

        with m.FSM(reset="WAITING"):
            with m.State("WAITING"):
                with m.If(uart.tx.rdy):
                    with m.If(pps_good_flag):
                        m.d.comb += [
                            uart.tx.ack.eq(True),
                            uart.tx.data.eq(SerialOutCodes.PPS_GOOD),
                        ]
                        m.d.sync += pps_good_flag.eq(False)
                        m.next = "SET_TX_TO_ZERO"
                    with m.If(pps_late_flag):
                        m.d.comb += [
                            uart.tx.ack.eq(True),
                            uart.tx.data.eq(SerialOutCodes.PPS_LATE),
                        ]
                        m.d.sync += pps_late_flag.eq(False)
                        m.next = "SET_TX_TO_ZERO"
                    with m.If(pps_early_flag):
                        m.d.comb += [
                            uart.tx.ack.eq(True),
                            uart.tx.data.eq(SerialOutCodes.PPS_EARLY),
                        ]
                        m.d.sync += pps_early_flag.eq(False)
                        m.next = "SET_TX_TO_ZERO"
            with m.State("SET_TX_TO_ZERO"):
                with m.If(uart.tx.rdy):
                    m.d.comb += [
                        uart.tx.ack.eq(True),
                        uart.tx.data.eq(SerialOutCodes.NOTHING),
                    ]
                    m.next = "WAITING"
        return m
