#!/usr/bin/env python3

from enum import Enum
from amaranth import *
from amaranth.back.rtlil import Case
from amaranth.lib.wiring import Component, In, Out

from amaranth_twstft.amaranth_serial import AsyncSerial, Parity
from amaranth_twstft.calibration_output import CalibrationMode
from amaranth_twstft.time_coder import TimeCoderMode, TIMECODE_SIZE
from amaranth_twstft.mixer import Mode
from amaranth_twstft.common import SerialInCommands, SerialOutCodes

class UARTWrapper(Component):
    def __init__(self, clk_freq, bitlen, pins):
        super().__init__({
            # Modifiable config
            'mode': Out(Shape.cast(Mode)),
            'timecoder_mode': Out(Shape.cast(TimeCoderMode)),
            'calib_mode': Out(Shape.cast(CalibrationMode)),
            'taps_a': Out(bitlen),
            'taps_b': Out(bitlen),

            # set time
            'set_time': Out(1),
            'time': Out(TIMECODE_SIZE),

            # flags
            'calibration_done': In(1),
            'calibration_error': In(1),
            'pps_good': In(1),
            'pps_early': In(1),
            'pps_late': In(1),
            'code_unaligned': In(1),
            'symbol_unaligned': In(1),
            'oscil_unaligned': In(1),
            })
        self.clk_freq = clk_freq
        self.pins = pins

    def elaborate(self, platform):
        m = Module()

        data_bits = 8
        m.submodules.uart = uart = AsyncSerial(
                divisor=int(self.clk_freq // 115200),
                data_bits=data_bits,
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
        code_unaligned_flag = Signal()
        with m.If(self.code_unaligned):
            m.d.sync += code_unaligned_flag.eq(True)
        symbol_unaligned_flag = Signal()
        with m.If(self.symbol_unaligned):
            m.d.sync += symbol_unaligned_flag.eq(True)
        oscil_unaligned_flag = Signal()
        with m.If(self.oscil_unaligned):
            m.d.sync += oscil_unaligned_flag.eq(True)
        calibration_done_flag = Signal()
        with m.If(self.calibration_done):
            m.d.sync += calibration_done_flag.eq(True)
        calibration_error_flag = Signal()
        with m.If(self.calibration_error):
            m.d.sync += calibration_error_flag.eq(True)

        # raise internal flags
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

        m.d.sync += uart.tx.ack.eq(False)

        with m.FSM(reset="WAITING"):
            def recv_in_reg(state: str, reg: Signal, next_state:str='WAITING'):
                """
                this function create all FSM states necessary
                to recieve an integer (in big endian),
                fitting in the register `reg`,
                by recieving `ceil(len(reg)//data_bits)` packets of `data_bits` bits.
                To start recieving, the FSM should be set to `state`,
                and once enough packets have been recieved,
                the FSM goes to `next_state`: 'WAITING' by default.
                The extra bits of the last packets are discarded.

                Warning : There is no timeout implemented yet and if not enouth packets are sent,
                          the FSM will be locked indefinitly.
                """
                for i in range(0, len(reg), data_bits):
                    name = state if i == 0 else f'__{state}__{i}'
                    name_next = (f'__{state}__{i+data_bits}'
                                 if i < len(reg) - data_bits else
                                 next_state)
                    with m.State(name):
                        m.d.comb += uart.rx.ack.eq(True)
                        with m.If(uart.rx.rdy):
                            m.d.sync += reg[i:i+data_bits].eq(uart.rx.data)
                            m.next = name_next

            recv_in_reg("SET_TAPS_A", self.taps_a)
            recv_in_reg("SET_TAPS_B", self.taps_b)
            recv_in_reg("SET_TIME", self.time, next_state="SET_TIME_FINISH")
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
                        with m.Case(SerialInCommands.MODE_OFF):
                            m.d.sync += self.mode.eq(Mode.OFF)
                        with m.Case(SerialInCommands.SET_TAPS_A):
                            m.next = "SET_TAPS_A"
                        with m.Case(SerialInCommands.SET_TAPS_B):
                            m.next = "SET_TAPS_B"
                        with m.Case(SerialInCommands.SET_TIME):
                            m.next = "SET_TIME"
                        with m.Case(SerialInCommands.TIMECODER_OFF):
                            m.d.sync += self.timecoder_mode.eq(TimeCoderMode.OFF)
                        with m.Case(SerialInCommands.TIMECODER_INVERT_FIRST_CODE):
                            m.d.sync += self.timecoder_mode.eq(TimeCoderMode.INVERT_FIRST_CODE)
                        with m.Case(SerialInCommands.TIMECODER_TIMECODE):
                            m.d.sync += self.timecoder_mode.eq(TimeCoderMode.TIMECODE)
                        with m.Case(SerialInCommands.CALIB_OFF):
                            m.d.sync += self.calib_mode.eq(CalibrationMode.OFF)
                        with m.Case(SerialInCommands.CALIB_CLK):
                            m.d.sync += self.calib_mode.eq(CalibrationMode.CLK)
                        with m.Case(SerialInCommands.CALIB_PPS):
                            m.d.sync += self.calib_mode.eq(CalibrationMode.PPS)
                        with m.Case(SerialInCommands.CALIB_AUTO):
                            m.d.sync += self.calib_mode.eq(CalibrationMode.AUTO)
                        with m.Default():
                            m.d.sync += unknown_command_flag.eq(True)
                with m.If(uart.tx.rdy):
                    def if_flag_send(flag: Signal, code: int, reset: bool = True, is_elif=False):
                        """
                        This helper function create the logic to send `code` if `flag` is up.
                        If `reset` is True, the `flag` is lowered, so `code` is only sent once.
                        If `flag` is lowered elsewhere, you want `reset` to be False.
                        """
                        with m.Elif(flag) if is_elif else m.If(flag):
                            m.d.sync += [
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
                    elif_flag_send(code_unaligned_flag, SerialOutCodes.CODE_UNALIGNED)
                    elif_flag_send(symbol_unaligned_flag, SerialOutCodes.SYMBOL_UNALIGNED)
                    elif_flag_send(oscil_unaligned_flag, SerialOutCodes.OSCIL_UNALIGNED)
                    elif_flag_send(rx_overflow_flag, SerialOutCodes.SERIAL_RX_OVERFLOW_ERROR)
                    elif_flag_send(rx_frame_flag, SerialOutCodes.SERIAL_RX_FRAME_ERROR)
                    elif_flag_send(rx_parity_flag, SerialOutCodes.SERIAL_RX_PARITY_ERROR)
                    elif_flag_send(calibration_done_flag, SerialOutCodes.CALIBRATION_DONE)
                    elif_flag_send(calibration_error_flag, SerialOutCodes.CALIBRATION_ERROR)
            with m.State("SET_TX_TO_ZERO"):
                with m.If(uart.tx.rdy):
                    m.d.sync += [
                        uart.tx.ack.eq(True),
                        uart.tx.data.eq(SerialOutCodes.NOTHING),
                    ]
                    m.next = "WAITING"
            with m.State("SET_TIME_FINISH"):
                m.d.comb += self.set_time.eq(True)
                m.next = "WAITING"

        return m
