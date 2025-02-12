from enum import Enum

from amaranth import ClockSignal, Module, Shape
from amaranth.lib.wiring import Component, In, Out


class CalibrationMode(Enum):
    OFF = 0
    CLK = 1
    PPS = 2

class CalibrationOutput(Component):
    mode: In(Shape.cast(CalibrationMode))
    pps: In(1)

    out: Out(1)

    def elaborate(self, plateform):
        m = Module()

        with m.Switch(self.mode):
            with m.Case(CalibrationMode.CLK):
                m.d.comb += self.out.eq(ClockSignal('sync'))
            with m.Case(CalibrationMode.PPS):
                m.d.comb += self.out.eq(self.pps)
            with m.Default():
                m.d.comb += self.out.eq(0)

        return m
