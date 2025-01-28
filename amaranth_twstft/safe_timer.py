from math import ceil
from amaranth import Module, Signal
from amaranth.lib.wiring import Component, In, Out
from amaranth.sim import Simulator, SimulatorContext


class SafeTimer(Component):
    """
    A timer that count down each tick until at 0
    this implementation mitigate combinatorial logic delays
    at the cost of control over the counter.
    The only property that is granted is that the counter
    will reach 0 `n` ticks after being reset.
    """
    reset: In(1) # the counter will start once reset is down
    finished: Out(1)

    def __init__(self, n: int, max_safe_size:int = 8):
        super().__init__()
        self.n = n
        assert n > 0
        self.max_safe_size = max_safe_size

    def elaborate(self, platform):
        m = Module()

        counter = Signal(range(self.n))
        ith_chunk_underflow = Signal(int(len(counter)//self.max_safe_size))

        with m.If(~self.finished):
            for i in range(len(ith_chunk_underflow) + 1):
                with m.If(ith_chunk_underflow[:i].all()):
                    chunk = counter[i*self.max_safe_size:(i+1)*self.max_safe_size]
                    m.d.sync += chunk.eq(chunk - 1)
                    if i < len(ith_chunk_underflow): # not the last chunk
                        m.d.sync += ith_chunk_underflow[i].eq(chunk == 1) # set underflow flag

        with m.If(counter == 1):
            m.d.sync += self.finished.eq(True) # next tick, counter will be zero

        with m.If(self.reset):
            m.d.sync += counter.eq(self.n)
            m.d.sync += self.finished.eq(False)
            for i, flag in enumerate(ith_chunk_underflow):
                nchunk = self.n >> (i*self.max_safe_size)
                nchunk &= 2**self.max_safe_size - 1
                m.d.sync += flag.eq(nchunk == 0)

        return m

if __name__ == '__main__':
    n = int(2**12 - 1)
    timer = SafeTimer(n, 3)
    sim = Simulator(timer)
    async def test_timer(ctx: SimulatorContext):
        for _ in range(5):
            ctx.set(timer.reset, True)
            await ctx.tick()
            ctx.set(timer.reset, False)
            for _ in range(n):
                assert not ctx.get(timer.finished)
                await ctx.tick()
            assert ctx.get(timer.finished)

    sim.add_testbench(test_timer)
    sim.add_clock(1)
    with sim.write_vcd('test_safe_timer.vcd'):
        sim.run()
