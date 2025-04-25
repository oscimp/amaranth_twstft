from enum import Enum
from amaranth import Module, Shape, Signal
from amaranth.sim import Simulator, SimulatorContext
from amaranth.lib.wiring import Component, In, Out

from amaranth_twstft.oscillator import Oscillator
from amaranth_twstft.common import Mode

class Mixer(Component):
    carrier: In(1)
    carrier90: In(1)
    data: In(2)
    time_code_data: In(1)
    mode: In(Shape.cast(Mode))

    out: Out(1)

    def elaborate(self, plateform):
        m = Module()

        out = Signal()

        with m.Switch(self.mode):
            with m.Case(Mode.CARRIER):
                m.d.comb += out.eq(self.carrier)
            with m.Case(Mode.BPSK):
                m.d.comb += out.eq(self.carrier ^ self.data[0])
            with m.Case(Mode.QPSK):
                carrier_axis = Signal()
                with m.If(self.data[0] ^ self.data[1]):
                    m.d.comb += carrier_axis.eq(self.carrier)
                with m.Else():
                    m.d.comb += carrier_axis.eq(self.carrier90)
                m.d.comb += out.eq(self.data[0] ^ carrier_axis)

        with m.If(self.mode != Mode.OFF):
            m.d.comb += self.out.eq(out ^ self.time_code_data)
        with m.Else():
            m.d.comb += self.out.eq(0)

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
