from amaranth import Assert, Module, Shape, Signal
from amaranth.lib.wiring import Component, In, Out
from amaranth.sim import Simulator, SimulatorContext, TriggerCombination

from amaranth_twstft.safe_timer import SafeTimer
from amaranth_twstft.mixer import Mode
from amaranth_twstft.oscillator import Oscillator
from amaranth_twstft.prn import PrnGenerator, nextstate

class Synchronizer(Component):
    """
    This module synchronize all timey components:
    - both PRN generators,
    - the carrier oscillator,
    - and the time coder
    """

    pps: In(1)

    next_code: Out(1)
    data: Out(2)

    # error flags:
    code_unaligned: Out(1) # last code didn't finish in time with pps
    symbol_unaligned: Out(1)
    oscil_unaligned: Out(1)

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
        m.submodules.symbols_counter = symbols_counter = SafeTimer(self.code_len)

        m.d.comb += self.data[0].eq(self.prn_a.state[0])

        m.d.comb += self.data[1].eq(self.prn_b.state[0])

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
                with m.If(symbols_counter.finished):
                    # when this path is active, next tick is a new sequance
                    m.d.comb += symbols_counter.reset.eq(True)
                    # same-tick reset the LFSRs
                    m.d.sync += self.prn_a.reset.eq(True)
                    m.d.sync += self.prn_b.reset.eq(True)

                    # the time-coder will be shifted next tick
                    m.d.comb += self.next_code.eq(True)
                with m.Else():
                    m.d.comb += symbols_counter.tick.eq(True)
            with m.Else():
                m.d.sync += periods_counter.eq(periods_counter + 1)

        #debug_data = Signal.like(self.data)

        with m.If(self.pps):
            #m.d.sync += debug_data.eq(debug_data + 1)

            with m.If(~self.oscil.phase_end):
                m.d.comb += self.oscil_unaligned.eq(True)
            with m.If(periods_counter != self.periods_per_symbol - 1):
                m.d.comb += self.symbol_unaligned.eq(True)
            with m.If(~symbols_counter.finished):
                m.d.comb += self.code_unaligned.eq(True)

            m.d.sync += periods_counter.eq(0)
            m.d.comb += symbols_counter.reset.eq(True)
            m.d.sync += self.prn_a.reset.eq(True)
            m.d.sync += self.prn_b.reset.eq(True)
            m.d.sync += self.oscil.reset.eq(True)
            m.d.comb += self.next_code.eq(False)

        #m.d.comb += self.data.eq(debug_data)

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
