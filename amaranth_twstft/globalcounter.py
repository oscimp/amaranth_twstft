#!/usr/bin/env python3

from amaranth import *
from math import log


class GlobalCounter(Elaboratable):
    """A module that outputs 1 as long as it hasn't counted up to its max_val.
    Otherwise, outputs 0 until it is resetted.

    Parameters
    ----------
    counter_width :positive integer
        number of bits to use for the counter
    
    max_val : positive integer
        the counter counts up to this value

    reload : boolean
        when True counter is set to 0, otherwise counter stay at max_val until
        reset

    wait_first_reset: boolean
        when True counter is stopped until reset is asserted, otherwise counter
        start immediately

    Attributes
    ----------
    
    max_val : positive integer
        the counter counts up to this value

    output : Signal()
        the output of the counter

    reset : Signal()
        input signal to restart the counter

    enable : Signal()
        input signal to enable/disable the counter

    tick : Signal()
        input signal driving the counter speed

    counter : Signal(range(max_val))
        the value of the counter

    """
    def __init__(self, max_val, reload=True, wait_first_reset=True):
        self.reset    = Signal()
        self.enable   = Signal()
        self.tick     = Signal()
        self.output   = Signal(reset_less=True)
        self.counter  = Signal(range(max_val+1),
                               reset=max_val if wait_first_reset else 0,
                               name="globalCounter")
        self.overflow = Signal(reset_less=True)
        self._max_val = max_val
        self._reload  = reload

    def elaborate(self, platform):
        m = Module()

        reload = (self._reload and self.counter == self._max_val -1)

        cnt_next = Signal(range(self._max_val), reset_less=True)
        m.d.comb += [
            cnt_next.eq(Mux(reload, 0, self.counter + 1)),
        ]
        m.d.sync += [
            self.overflow.eq(cnt_next == self._max_val -1& self.tick),
            self.output.eq((cnt_next < self._max_val))
        ]

        with m.If(~self.enable):
            m.d.sync += self.counter.eq(self.counter.reset)
        with m.If(self.reset):
            m.d.sync += self.counter.eq(0)
        with m.Elif((self.counter < self._max_val) & self.tick):
            m.d.sync += self.counter.eq(cnt_next)

        return m
