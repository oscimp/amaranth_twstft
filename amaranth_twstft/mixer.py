from enum import Enum
from amaranth import Module, Shape, Signal
from amaranth.sim import Simulator, SimulatorContext
from amaranth.lib.wiring import Component, In, Out

from oscillator import Oscillator

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
                with m.If(self.data[0] ^ self.data[1]):
                    m.d.comb += carrier_axis.eq(self.carrier)
                with m.Else():
                    m.d.comb += carrier_axis.eq(self.carrier90)
                m.d.comb += self.out.eq(self.data[0] ^ carrier_axis)

        return m


if __name__ == '__main__':
    periode = 4
    m = Module()
    m.submodules.oscil = oscil = Oscillator(periode, 1)
    m.submodules.mixer = mixer = Mixer()
    m.d.comb += mixer.carrier.eq(oscil.out)
    m.d.comb += mixer.carrier90.eq(oscil.out90)
    sim = Simulator(m)
    sim.add_clock(1)
    async def test_mixer(ctx: SimulatorContext):
        await ctx.tick()
        ctx.set(mixer.mode, Mode.QPSK)
        ctx.set(oscil.reset, True)
        for data in range(4):
            ctx.set(mixer.data, data)
            for _ in range(periode * 10):
                await ctx.tick()
                ctx.set(oscil.reset, False)

    sim.add_testbench(test_mixer)
    with sim.write_vcd('test_mixer.vcd'):
        sim.run()
