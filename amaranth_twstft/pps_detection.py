from amaranth import Module, Signal
from amaranth.lib.wiring import Component, In, Out


class PPSDetector(Component):
    pps_in: In(1)
    pps: Out(1)
    
    def elaborate(self, plateform):
        m = Module()

        # synchronisation chain
        a = Signal()
        b = Signal()
        c = Signal()

        m.d.sync += a.eq(self.pps_in)
        m.d.sync += b.eq(a)
        m.d.sync += c.eq(b)

        m.d.comb += self.pps.eq(b & ~c)

        ## the rest of the module is for error/unexpected behavior detection
        # unexpected pps signals and late pps signals

        return m
