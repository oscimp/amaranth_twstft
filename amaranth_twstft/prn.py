#!/usr/bin/env python3

from amaranth import *
from amaranth.lib.wiring import Component, In, Out
from amaranth.sim import *

from amaranth_twstft.common import nextstate

#default number of different taps to choose among when dynamically selecting the taps for the LFSR
nb_taps_auto = 32

class PrnGenerator(Component):
    """
        A LFSR with same-tick-action shift and reset.
        The taps and the seed can be modified at runtime.
    """
    def __init__(self, bit_len, taps=None, seed=1):
        assert bit_len > 1
        super().__init__({
            "reset": In(1),
            "shift": In(1),
            "taps": In(bit_len),
            "seed": In(bit_len),
            "state": Out(bit_len)
            })
        self.bit_len = bit_len
        self._taps = taps
        self._seed = seed

    def elaborate(self, platform):
        m = Module()

        reg = Signal(self.bit_len, reset_less=True)

        if self._taps is not None:
            m.d.comb += self.taps.eq(self._taps)

        if self._seed is not None:
            m.d.comb += self.seed.eq(self._seed)

        m.d.comb += self.state.eq(reg)

        with m.If(self.shift):
            insert = (reg & self.taps).xor()
            new_state = Cat(reg[1:], insert)
            m.d.comb += self.state.eq(new_state)
            m.d.sync += reg.eq(new_state)

        with m.If(self.reset):
            m.d.comb += self.state.eq(self.seed)
            m.d.sync += reg.eq(self.seed)

        return m

class PrnGeneratorTest(Simulator):
    def __init__(self):
        self.bit_len = 14
        self.taps = 3
        self.seed = 1
        self.dut = PrnGenerator(self.bit_len, self.taps, self.seed)
        super().__init__(self.dut)
        self.add_clock(1)
        self.add_testbench(self.test_pnr)

    async def test_pnr(self, ctx: SimulatorContext):
        ctx.set(self.dut.reset, True)
        assert ctx.get(self.dut.state) == self.seed
        await ctx.tick()
        ctx.set(self.dut.reset, False)
        for _ in range(5):
            assert ctx.get(self.dut.state) == self.seed
            await ctx.tick()
        state = self.seed
        for _ in range(5):
            ctx.set(self.dut.shift, True)
            state = nextstate(state, self.taps, self.bit_len)
            assert ctx.get(self.dut.state) == state
            await ctx.tick()
            ctx.set(self.dut.shift, False)
            assert ctx.get(self.dut.state) == state
            await ctx.tick()
            assert ctx.get(self.dut.state) == state
        ctx.set(self.dut.shift, True)
        for _ in range(5):
            state = nextstate(state, self.taps, self.bit_len)
            assert ctx.get(self.dut.state) == state
            await ctx.tick()
        ctx.set(self.dut.reset, True)
        assert ctx.get(self.dut.state) == self.seed
        await ctx.tick()
        ctx.set(self.dut.reset, False)
        ctx.set(self.dut.shift, False)
        assert ctx.get(self.dut.state) == self.seed

if __name__ == "__main__":
    PrnGeneratorTest().run()
