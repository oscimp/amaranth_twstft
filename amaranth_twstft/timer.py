#!/usr/bin/env python3

from amaranth import *

class Timer(Elaboratable):
    def __init__(self, timeout):
        self.timeout = timeout
        self.timer   = Signal(range(0, self.timeout), reset=0)
        self.fire    = Signal(reset_less=True)
        self.enable  = Signal()

    def elaborate(self, platform):
        m = Module()

        enable_int = Signal()
        fire_int   = Signal()
        timer_next = Signal.like(self.timer)

        m.d.sync += self.fire.eq(fire_int)
        m.d.comb += fire_int.eq(timer_next == self.timeout -1)
        with m.If(self.enable):
            m.d.sync += enable_int.eq(1)
        with m.Elif(fire_int):
            m.d.sync += enable_int.eq(0)

        m.d.comb += timer_next.eq(self.timer + 1)

        m.d.sync += self.timer.eq(Mux(self.enable | enable_int, timer_next, 0))

        return m
