from enum import Enum
from amaranth import Module, Shape, Signal
from amaranth.lib.wiring import Component, In, Out

class Mode(Enum):
    CARRIER = 0
    BPSK = 1
    QPSK = 2

class Mixer(Component):
    carrier: In(1)
    carrier90: In(1)
    data: In(2)
    mode: In(Shape.cast(Mode))
    out: Out(1)

    def elaborate(self, plateform):
        m = Module()

        with m.Switch(self.mode):
            with m.Case(Mode.CARRIER):
                m.d.comb += self.out.eq(self.carrier)
            with m.Case(Mode.BPSK):
                m.d.comb += self.out.eq(self.carrier ^ self.data[0])
            with m.Case(Mode.QPSK):
                carrier_axis = Signal()
                with m.If(self.data[1]):
                    m.d.comb += carrier_axis.eq(self.carrier90)
                with m.Else():
                    m.d.comb += carrier_axis.eq(self.carrier)
                m.d.comb += self.out.eq(self.data[0] ^ carrier_axis)

        return m
