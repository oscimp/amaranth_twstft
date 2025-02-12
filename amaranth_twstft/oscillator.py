from amaranth import *
from amaranth.lib.wiring import *
from amaranth.sim import Simulator, SimulatorContext

import inspect

class Oscillator(Component):
    """
        An oscillator with same-tick-action reset.
    """
    reset: In(1)
    out: Out(1)
    out90: Out(1)
    phase_end: Out(1)

    def __init__(self, f_clock: int, f_out: int):
        assert f_clock % (f_out*4) == 0, f"Quadruple oscillator's freq e{f_out} * 4 = {f_out*4} Hz) has to divide the clock's freq ({f_clock} Hz)"
        super().__init__()
        self._tick_per_period = f_clock // f_out

    def elaborate(self, platform):
        m = Module()

        counter = Signal(range(self._tick_per_period))

        m.d.comb += self.phase_end.eq(counter == self._tick_per_period - 1)
        with m.If(self.phase_end):
            m.d.sync += counter.eq(0)
        with m.Else():
            m.d.sync += counter.eq(counter + 1)

        m.d.comb += self.out.eq(counter < self._tick_per_period//2)
        m.d.comb += self.out90.eq((counter >= self._tick_per_period//4) &
                                  (counter < self._tick_per_period*3 //4))

        with m.If(self.reset):
            m.d.sync += counter.eq(1)
            m.d.comb += self.phase_end.eq(False)
            m.d.comb += self.out.eq(True)
            m.d.comb += self.out90.eq(False)

        return m


class OscilatorTest(Simulator):
    def __init__(self):
        self.period = 4
        self.dut = Oscillator(self.period, 1)
        super().__init__(self.dut)
        self.add_clock(1 / self.period)
        self.add_testbench(self.test_oscill)

    async def test_oscill(self, ctx: SimulatorContext):
        ctx.set(self.dut.reset, True)
        for _ in range(5):
            for _ in range(self.period//2):
                assert ctx.get(self.dut.out) == True
                await ctx.tick()
                ctx.set(self.dut.reset, False)
            for _ in range(self.period//2):
                assert ctx.get(self.dut.out) == False
                await ctx.tick()

        for _ in range(self.period//4):
            await ctx.tick()
        for _ in range(self.period//2):
            assert ctx.get(self.dut.out90) == True
            await ctx.tick()
        for _ in range(self.period//2):
            assert ctx.get(self.dut.out90) == False
            await ctx.tick()



if __name__ == "__main__":
    OscilatorTest().run()

