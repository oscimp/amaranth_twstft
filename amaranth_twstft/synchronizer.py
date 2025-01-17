from amaranth import Assert, Module, Shape, Signal
from amaranth.lib.wiring import Component, In, Out
from amaranth.sim import Simulator, SimulatorContext, TriggerCombination

from mixer import Mode
from oscillator import Oscillator
from prn import PrnGenerator, nextstate

class Synchronizer(Component):
    pps: In(1)
    mode: In(Shape.cast(Mode))
    data: Out(2)

    def __init__(self, prn: PrnGenerator, code_len:int, ticks_per_bit: int, oscil: Oscillator):
        super().__init__()
        self.prn = prn
        self.code_len = code_len
        self.ticks_per_bit = ticks_per_bit
        self.oscil = oscil

    def elaborate(self, platform):
        m = Module()

        bits_count = Signal(range(self.code_len)) # number of bits (pairs of bits in QPSK) transmitted
        ticks_count = Signal(range(self.ticks_per_bit))
        shift_count = Signal(2, init=2) # nb of prn shifts done in QPSK

        with m.If(ticks_count == self.ticks_per_bit - 1):
            m.d.sync += ticks_count.eq(0)
        with m.Else():
            m.d.sync += ticks_count.eq(ticks_count + 1)

        with m.If(ticks_count == 0):
            with m.If(bits_count == self.code_len - 1):
                m.d.sync += bits_count.eq(0)
            with m.Else():
                with m.If(bits_count == 0):
                    m.d.comb += self.prn.reset.eq(True)
                m.d.sync += bits_count.eq(bits_count + 1)

        with m.If(self.mode == Mode.BPSK):
            m.d.comb += self.prn.shift.eq(ticks_count == 0)
            m.d.sync += self.data[0].eq(self.prn.state[0])

        with m.Elif(self.mode == Mode.QPSK):
            with m.If(ticks_count == 0):
                m.d.sync += shift_count.eq(0)
                m.d.sync += self.data.eq(self.prn.state[:2])
            with m.If(shift_count < 2):
                m.d.comb += self.prn.shift.eq(True)
                m.d.sync += shift_count.eq(shift_count + 1)


        with m.If(self.pps):
            m.d.sync += bits_count.eq(0) # also reset prn in the same tick that bits_count == 0
            m.d.sync += shift_count.eq(2)
            m.d.sync += ticks_count.eq(0)
            m.d.sync += self.oscil.reset.eq(True)
        with m.Else():
            m.d.sync += self.oscil.reset.eq(False)

        return m


class SynchronizerTest(Simulator):
    def __init__(self):
        self.oscil_len = 4
        self.ticks_per_bit = 2 * self.oscil_len
        self.code_len = 50
        m = Module()
        m.submodules.o = oscil = Oscillator(self.oscil_len, 1)
        self.taps = 43
        self.seed = 1
        m.submodules.prn = prn = PrnGenerator(14, self.taps, self.seed)
        m.submodules.s = self.dut = Synchronizer(prn, self.code_len, self.ticks_per_bit, oscil)
        super().__init__(m)
        self.add_clock(1)

    async def test_sync_bpsk(self, ctx: SimulatorContext):
        ctx.set(self.dut.mode, Mode.BPSK)
        ctx.set(self.dut.pps, True)
        await ctx.tick()
        ctx.set(self.dut.pps, False)
        for _ in range(5):
            state = self.seed
            for _ in range(self.code_len):
                for _ in range(self.ticks_per_bit):
                    await ctx.tick()
                    assert ctx.get(self.dut.data[0]) == state % 2
                state = nextstate(state, self.taps, 14)

    async def test_sync_qpsk(self, ctx: SimulatorContext):
        ctx.set(self.dut.mode, Mode.QPSK)
        for _ in range(42):
            await ctx.tick()
        ctx.set(self.dut.pps, True)
        await ctx.tick()
        ctx.set(self.dut.pps, False)
        for _ in range(5):
            state = self.seed
            for _ in range(self.code_len):
                for _ in range(self.ticks_per_bit):
                    await ctx.tick()
                    assert ctx.get(self.dut.data) == state % 4
                state = nextstate(state, self.taps, 14)
                state = nextstate(state, self.taps, 14)

if __name__ == "__main__":
    tests = SynchronizerTest()
    tests.add_testbench(tests.test_sync_bpsk)
    tests.run()
    tests = SynchronizerTest()
    tests.add_testbench(tests.test_sync_qpsk)
    tests.run()
