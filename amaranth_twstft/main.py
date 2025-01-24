from amaranth import Module, Shape, Signal
from amaranth.lib.wiring import Component, In, Out
from amaranth.sim import Simulator, SimulatorContext
from amaranth_boards.resources import *

from uart_wrapper import UARTWrapper
from synchronizer import Synchronizer 
from mixer import Mixer, Mode
from oscillator import Oscillator
from pps_detection import PPSDetector
from prn import PrnGenerator


class TwstftMain(Component):
    pps: In(1)
    antena_out: Out(1)

    def __init__(
            self,
            f_clock,
            f_carrier,
            f_code, 
            code_len=10**4,
            mode=Mode.QPSK,
            bit_len=14,
            taps_a=43,
            seed_a=1,
            taps_b=3,
            seed_b=1,
            uart=None,
            ):
        super().__init__()
        self.f_clock = f_clock
        self.f_carrier = f_carrier
        self.f_code = f_code
        assert f_clock % f_carrier == 0
        assert f_carrier % f_code == 0
        self.code_len = code_len
        self.bit_len = bit_len
        self.taps_a = taps_a
        self.seed_a = seed_a
        self.taps_b = taps_b
        self.seed_b = seed_b
        self.uart = uart

    def elaborate(self, platform):
        m = Module()

        # Config
        #taps_a = Signal(self.bit_len)
        #seed_a = Signal(self.bit_len)
        #taps_b = Signal(self.bit_len)
        #seed_b = Signal(self.bit_len)

        #m.d.comb += taps_a.eq(self.taps_a)
        #m.d.comb += seed_a.eq(self.seed_a)
        #m.d.comb += taps_b.eq(self.taps_b)
        #m.d.comb += seed_b.eq(self.seed_b)

        # Modules
        m.submodules.pps = mpps = PPSDetector(self.f_clock)
        print(self.taps_a, self.taps_b)
        m.submodules.prn_a = prn_a = PrnGenerator(self.bit_len, taps=self.taps_a)
        m.submodules.prn_b = prn_b = PrnGenerator(self.bit_len, taps=self.taps_b)
        m.submodules.oscil = oscil = Oscillator(self.f_clock, self.f_carrier)
        m.submodules.synchronizer = synchronizer = Synchronizer(
                prn_a,
                prn_b,
                self.code_len,
                self.f_carrier // self.f_code,
                oscil)
        m.submodules.mixer = mixer = Mixer()

        m.submodules.uart = uart = UARTWrapper(
                self.f_clock,
                self.bit_len,
                self.uart)


        # Connexions

        m.d.comb += mpps.pps_in.eq(self.pps)

        m.d.comb += uart.pps_good.eq(mpps.pps_good)
        m.d.comb += uart.pps_late.eq(mpps.pps_late)
        m.d.comb += uart.pps_early.eq(mpps.pps_early)

        m.d.comb += synchronizer.pps.eq(mpps.pps)
        m.d.comb += synchronizer.invert_first_code.eq(False)

        #m.d.comb += prn_a.taps.eq(taps_a)
        #m.d.comb += prn_a.seed.eq(seed_a)
        #m.d.comb += prn_b.taps.eq(taps_b)
        #m.d.comb += prn_b.seed.eq(seed_b)

        m.d.comb += mixer.carrier.eq(oscil.out)
        m.d.comb += mixer.carrier90.eq(oscil.out90)
        m.d.comb += mixer.data.eq(synchronizer.data)
        m.d.comb += mixer.mode.eq(uart.mode)

        m.d.comb += self.antena_out.eq(mixer.out)

        return m

if __name__ == '__main__':
    dut = TwstftMain(
            2800000,
            70000,
            2500,
            uart=None)
    sim = Simulator(dut)
    sim.add_clock(1/2800000)

    async def process(ctx: SimulatorContext):
        i = 0
        while True:
            await ctx.tick()
            if i == 10:
                ctx.set(dut.pps, True)
            elif i == 100:
                ctx.set(dut.pps, False)
            i = (i + 1) % 2800000

    sim.add_process(process)

    with sim.write_vcd('global_sim.vcd'):
        sim.run_until(4)
