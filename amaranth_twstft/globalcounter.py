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

    tick : Signal()
        input signal driving the counter speed

    counter : Signal(range(max_val))
        the value of the counter

    """
    def __init__(self, max_val, reload=True, wait_first_reset=True):
        self._max_val = max_val
        self.reset    = Signal()
        self.tick     = Signal()
        self.output   = Signal()
        self.counter  = Signal(range(max_val),
                               reset=max_val if wait_first_reset else 0,
                               name="globalCounter")
        self.overflow = Signal()
        self._reload  = reload

    def elaborate(self, platform):
        m = Module()

        reload = (self._reload and self.counter == self._max_val -1)

        m.d.comb += self.overflow.eq(reload)

        with m.If(self.counter == self._max_val):
            m.d.sync += self.output.eq(0)
        with m.Else():
            m.d.sync += [self.output.eq(1)]
            with m.If(self.tick):
                with m.If(reload):
                    m.d.sync += [
                        self.counter.eq(0),
                        #self.overflow.eq(1)
                    ]
                with m.Else():
                    m.d.sync += self.counter.eq(self.counter + 1)
        with m.If(self.reset):
            m.d.sync += self.counter.eq(0)

        return m
