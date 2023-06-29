#!/usr/bin/env python3

from amaranth import *
from amaranth_stdio.serial import AsyncSerial
from amaranth_twstft.timer import Timer


class UARTWrapper(Elaboratable):
    """A synchronizable version of the n-bits PRN Generator to use along the 1-PPS Signal

    Parameters
    ----------
    bit_len : greater than 1 integer
        the number of bits of our LFSR
    
    taps : less than 2^(bit_len)-1 positive integer
        the taps to apply to our LFSR
        if set to zero, we consider the taps as dynamically 
        chosen by the signal `tsel` (see below attributes)

    seed : less than 2^(bit_len)-1 non-zero positive integer
        the initial state of the LFSR
        (1 by default)


    Attributes
    ----------
    output : Signal()
        the output of the LFSR
        
    reg : Signal(bit_len)
        the LFSR used to compute the prn

    enable : Signal()
        the enable signal of the PRN Generator 
        keeps the LFSR in its initial state as long as the signal is set to 0

    next : Signal()
        shifts the LFSR on every rising clock edge as long as it is set to 1

    tsel : Signal(x)
        x corresponds to the number of bits required to 
        count up to the number of taps stored.
        (5 by default as there are at most 32 different taps stored 
        (change it by resetting the value of nb_taps_auto))
        Its value corresponds to the address of the taps stored in memory
        when driven from outside the module, allows to change dynamically 
        the taps used on our LFSR. 
        This can only be used when the `taps` parameter is 0

    _dynamic_tsel : Boolean
        true when taps are defined dynamically

    _mem : Memory()
        the place where dynamically used taps are stored
        Only exists when the `taps` parameter is 0

    _taps : Signal(20)
        signal used as taps for the LFSR
    """
    
    def __init__(self, clk_freq, uart_pads=None):
        #check for a few assertions before working
        assert uart_pads is not None

        # input signal
        self.rise_pps = Signal(reset_less=True) # used to start request
        # output signals
        self.date_en  = Signal()
        self.date_val = Signal(range(60))

        self._uart_pads = uart_pads
        self._clk_freq  = clk_freq

    def elaborate(self, platform):
        m = Module()

        m.submodules.timer = timer = Timer(int(self._clk_freq/2))

        uart = AsyncSerial(divisor=int(self._clk_freq // 115200),
                           pins=self._uart_pads)
        m.submodules.uart = uart

        rdy_old   = Signal()
        m.d.sync += rdy_old.eq(uart.rx.rdy)
        uart_rdy  = (~rdy_old & uart.rx.rdy)

        m.d.comb += [
            uart.tx.ack.eq(0),
            uart.rx.ack.eq(0)
        ]

        m.d.sync += [
            self.date_en.eq(0),
            timer.enable.eq(0),
        ]

        with m.FSM(reset="WAIT_PPS") as fsm:
            with m.State("WAIT_PPS"):
                with m.If(self.rise_pps):
                    m.d.comb += [
                        uart.tx.ack.eq(1),
                        uart.tx.data.eq(self.date_val),
                    ]
                    m.d.sync += timer.enable.eq(1)
                    m.next = "WAIT_PC"
            with m.State("WAIT_PC"):
                m.d.comb += uart.rx.ack.eq(1)
                #m.d.sync += timer.enable.eq(1)
                with m.If(uart_rdy):
                    m.d.sync += [
                        self.date_val.eq(uart.rx.data),
                        self.date_en.eq(1),
                    ]
                    m.next = "WAIT_PPS"
                with m.Elif(timer.fire):
                    m.next = "WAIT_PPS"
        return m
