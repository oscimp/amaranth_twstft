from math import ceil
from amaranth import Module, Signal
from amaranth.lib.wiring import Component, In, Out
from amaranth.sim import Simulator, SimulatorContext


class SafeTimer(Component):
    """
    A timer that count down each time it's ticked until at 0
    this implementation mitigate combinatorial logic delays
    at the cost of control over the counter.
    The only property that is granted is that the counter
    will reach 0 `n` ticks after being reset.
    """
    reset: In(1) # the counter will start once reset is down
    tick: In(1) # the counter decrement one each clock cycle where tick is True
    finished: Out(1)

    def __init__(self, n: int, chunk_size:int = 8):
        super().__init__()
        assert n > 0
        self.n = n
        self.chunk_size = chunk_size

    def elaborate(self, platform):
        m = Module()

        counter = Signal(range(self.n), reset_less=True)
        ith_chunk_underflow = Signal(int(len(counter)//self.chunk_size), reset_less=True)

        with m.If(~self.finished & self.tick):
            for i in range(len(ith_chunk_underflow) + 1):
                with m.If(ith_chunk_underflow[:i].all()):
                    chunk = counter[i*self.chunk_size:(i+1)*self.chunk_size]
                    m.d.sync += chunk.eq(chunk - 1)
                    if i < len(ith_chunk_underflow): # not the last chunk
                        m.d.sync += ith_chunk_underflow[i].eq(chunk == 1) # set underflow flag

        with m.If(counter == 1):
            m.d.sync += self.finished.eq(True) # next tick, counter will be zero

        with m.If(self.reset):
            m.d.sync += counter.eq(self.n)
            m.d.sync += self.finished.eq(False)
            for i, flag in enumerate(ith_chunk_underflow):
                nchunk = self.n >> (i*self.chunk_size)
                nchunk &= 2**self.chunk_size - 1
                m.d.sync += flag.eq(nchunk == 0)

        return m

if __name__ == '__main__':
    n = int(2**12 - 1)
    timer = SafeTimer(n, 3)
    sim = Simulator(timer)
    async def test_timer(ctx: SimulatorContext):
        ctx.set(timer.tick, True)
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
