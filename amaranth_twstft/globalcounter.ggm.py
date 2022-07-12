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
    def __init__(self, max_val):
        self._max_val = max_val
        self.reset = Signal()
        self.tick = Signal()
        self.output = Signal()
        self.counter = Signal(range(max_val), reset=0, name="globalCounter")
        
    def elaborate(self, platform):
        m = Module()

        incr_n = Signal(reset=1)
        incr   = Signal(reset=1)

        m.d.comb += incr_n.eq(self.counter == self._max_val -1)
        m.d.sync += incr.eq(incr_n)
        #with m.If(self.counter == self._max_val):
        m.d.sync += self.output.eq(incr)
        #with m.Else():
        #if 1 == 1:
        with m.If(incr):
            #m.d.sync += [
            #    self.output.eq(1),
            #]
            with m.If(self.tick):
                m.d.sync += self.counter.eq(self.counter + 1)
        with m.If(self.reset):
            m.d.sync += self.counter.eq(0)
            
        return m
