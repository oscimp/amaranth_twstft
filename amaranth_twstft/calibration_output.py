from enum import Enum

from amaranth import ClockSignal, Module, Shape
from amaranth.lib.wiring import Component, In, Out

from amaranth_twstft.common import CalibrationMode

class CalibrationOutput(Component):
    mode: In(Shape.cast(CalibrationMode))
    pps: In(1)
    delayed_pps: In(1)

    out: Out(1)

    def elaborate(self, plateform):
        m = Module()

        with m.Switch(self.mode):
            with m.Case(CalibrationMode.CLK):
                m.d.comb += self.out.eq(ClockSignal('sync'))
            with m.Case(CalibrationMode.PPS):
                m.d.comb += self.out.eq(self.pps)
            with m.Case(CalibrationMode.AUTO):
                m.d.comb += self.out.eq(self.delayed_pps)
            with m.Default():
                m.d.comb += self.out.eq(0)

        return m
