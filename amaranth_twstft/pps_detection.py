from amaranth import Module, Signal
from amaranth.lib.wiring import Component, In, Out


class PPSDetector(Component):
    pps_in: In(1)
    pps: Out(1)

    # flags
    pps_good: Out(1)
    pps_late: Out(1)
    pps_early: Out(1)

    def __init__(self, f_clock):
        super().__init__()
        self.f_clock = f_clock

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

        counter = Signal(range(self.f_clock))
        with m.If((counter == self.f_clock - 1) & self.pps):
            m.d.comb += self.pps_good.eq(True)
            m.d.sync += counter.eq(0)
        with m.Elif(self.pps):
            m.d.comb += self.pps_early.eq(True)
            m.d.sync += counter.eq(0)
        with m.Elif(counter == self.f_clock - 1):
            m.d.comb += self.pps_late.eq(True)
            m.d.sync += counter.eq(0)
        with m.Else():
            m.d.sync += counter.eq(counter + 1)

        return m
