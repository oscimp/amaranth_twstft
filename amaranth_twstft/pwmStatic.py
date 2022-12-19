#!/usr/bin/env python3

from amaranth import *
from math import log


class PWMStatic(Elaboratable):
    """A module that outputs 1 until counter hasn't counted up to its duty_val
    and 0 when counter has counted up to duty_val but down to max_val.

    Parameters
    ----------
    duty_val : positive integer
        the counter counts up to this value

    max_val : positive integer
        the counter counts up to this value

    wait_first_reset: boolean
        when True counter is stopped until reset is asserted, otherwise counter
        start immediately

    Attributes
    ----------
    
    max_val : positive integer
        the counter counts up to this value

    duty_val : positive integer
        output signal is high until counter has counted to this value

    output : Signal()
        the output of the counter

    reset : Signal()
        input signal to restart the counter

    enable : Signal()
        input signal to enable/disable the counter

    counter : Signal(range(max_val))
        the value of the counter

    """
    def __init__(self, duty_val, max_val, wait_first_reset=True):
        self.reset    = Signal()
        self.enable   = Signal()
        self.output   = Signal(reset_less=True)
        self.counter  = Signal(range(max_val),
                               reset=max_val if wait_first_reset else 0,
                               name="pwmCounter")
        self._duty_val = duty_val
        self._max_val  = max_val

    def elaborate(self, platform):
        m = Module()

        reload = self.counter >= self._max_val -1

        cnt_next = Signal(range(self._max_val), reset_less=True)
        m.d.comb += [
            cnt_next.eq(Mux(reload, 0, self.counter + 1)),
            self.output.eq((self.counter < self._duty_val-1))
        ]

        with m.If(~self.enable):
            m.d.sync += self.counter.eq(self.counter.reset)
        with m.Elif(self.reset):
            m.d.sync += self.counter.eq(0)
        with m.Elif(self.counter < self._max_val):
            m.d.sync += self.counter.eq(cnt_next)

        return m
