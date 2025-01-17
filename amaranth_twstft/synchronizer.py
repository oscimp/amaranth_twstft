from amaranth import Assert, Module, Shape, Signal
from amaranth.lib.wiring import Component, In, Out
from amaranth.sim import Simulator, SimulatorContext, TriggerCombination

from mixer import Mode
from oscillator import Oscillator
from prn import PrnGenerator, nextstate

class Synchronizer(Component):
    pps: In(1)
    invert_first_code: In(1)
    data: Out(2)

    def __init__(
            self,
            prn_a: PrnGenerator,
            prn_b: PrnGenerator,
            code_len: int,
            periods_per_symbol: int,
            oscil: Oscillator):
        super().__init__()
        self.prn_a = prn_a
        self.prn_b = prn_b
        self.code_len = code_len
        self.periods_per_symbol = periods_per_symbol
        self.oscil = oscil

    def elaborate(self, platform):
        m = Module()

        # count the periods completed for each symbol to send
        periods_counter = Signal(range(self.periods_per_symbol))
        # count the symbols sent for each sequance
        symbols_counter = Signal(range(self.code_len))

        first_code = Signal() # True if we are sending the first code

        m.d.comb += self.data[0].eq(self.prn_a.state[0] ^
                                    (first_code & self.invert_first_code))
        m.d.comb += self.data[1].eq(self.prn_b.state[0] ^
                                    (first_code & self.invert_first_code))

        # maintain the resets and shifts at False by default
        m.d.sync += self.prn_a.reset.eq(False)
        m.d.sync += self.prn_b.reset.eq(False)
        m.d.sync += self.prn_a.shift.eq(False)
        m.d.sync += self.prn_b.shift.eq(False)
        m.d.sync += self.oscil.reset.eq(False)

        # increment periods_counter on the same tick that the new phase begin
        with m.If(self.oscil.phase_end):
            with m.If(periods_counter == self.periods_per_symbol - 1):
                # when this path is active, next tick is a new symbol
                m.d.sync += periods_counter.eq(0)
                # same-tick shift the LFSRs
                m.d.sync += self.prn_a.shift.eq(True)
                m.d.sync += self.prn_b.shift.eq(True)
                # increment symbols_counter on periods_counter overflow
                with m.If(symbols_counter == self.code_len - 1):
                    # when this path is active, next tick is a new sequance
                    m.d.sync += symbols_counter.eq(0)
                    # same-tick reset the LFSRs
                    m.d.sync += self.prn_a.reset.eq(True)
                    m.d.sync += self.prn_b.reset.eq(True)
                    m.d.sync += first_code.eq(False)
                with m.Else():
                    m.d.sync += symbols_counter.eq(symbols_counter + 1)
            with m.Else():
                m.d.sync += periods_counter.eq(periods_counter + 1)

        with m.If(self.pps):
            m.d.sync += periods_counter.eq(0)
            m.d.sync += symbols_counter.eq(0)
            m.d.sync += self.prn_a.reset.eq(True)
            m.d.sync += self.prn_b.reset.eq(True)
            m.d.sync += self.oscil.reset.eq(True)
            m.d.sync += first_code.eq(True)


        return m


class SynchronizerTest(Simulator):
    def __init__(self):
        self.oscil_len = 4
        self.periods_per_symbol = 8
        self.code_len = 50
        m = Module()
        m.submodules.o = oscil = Oscillator(self.oscil_len, 1)
        self.taps_a = 43
        self.taps_b = 3
        self.seed = 1
        m.submodules.prn_a = prn_a = PrnGenerator(14, self.taps_a, self.seed)
        m.submodules.prn_b = prn_b = PrnGenerator(14, self.taps_b, self.seed)
        m.submodules.s = self.dut = Synchronizer(
                prn_a,
                prn_b,
                self.code_len,
                self.periods_per_symbol,
                oscil)
        super().__init__(m)
        self.add_clock(1)

    async def test_sync_bpsk(self, ctx: SimulatorContext):
        ctx.set(self.dut.pps, True)
        await ctx.tick()
        ctx.set(self.dut.pps, False)
        for _ in range(5):
            state = self.seed
            for _ in range(self.code_len):
                for _ in range(self.periods_per_symbol*self.oscil_len):
                    assert ctx.get(self.dut.data[0]) == state % 2
                    await ctx.tick()
                state = nextstate(state, self.taps_a, 14)

    async def test_sync_qpsk(self, ctx: SimulatorContext):
        for _ in range(42):
            await ctx.tick()
        ctx.set(self.dut.pps, True)
        await ctx.tick()
        ctx.set(self.dut.pps, False)
        for _ in range(5):
            state_a = self.seed
            state_b = self.seed
            for _ in range(self.code_len):
                for _ in range(self.periods_per_symbol*self.oscil_len):
                    assert ctx.get(self.dut.data[0]) == state_a % 2
                    assert ctx.get(self.dut.data[1]) == state_b % 2
                    await ctx.tick()
                state_a = nextstate(state_a, self.taps_a, 14)
                state_b = nextstate(state_b, self.taps_b, 14)

if __name__ == "__main__":
    tests = SynchronizerTest()
    tests.add_testbench(tests.test_sync_bpsk)
    tests.run()
    tests = SynchronizerTest()
    tests.add_testbench(tests.test_sync_qpsk)
    tests.run()
