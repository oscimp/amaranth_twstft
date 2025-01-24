from amaranth import Module, Shape, Signal
from amaranth.lib.wiring import Component, In, Out
from amaranth.sim import Simulator, SimulatorContext
from amaranth_boards.resources import *

from time_coder import TimeCoder
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
        self.uart = uart

    def elaborate(self, platform):
        m = Module()

        # Modules
        m.submodules.pps = mpps = PPSDetector(self.f_clock)
        m.submodules.prn_a = prn_a = PrnGenerator(self.bit_len)
        m.submodules.prn_b = prn_b = PrnGenerator(self.bit_len)
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

        m.submodules.time = time = TimeCoder()


        # Connexions

        m.d.comb += mpps.pps_in.eq(self.pps)

        m.d.comb += uart.pps_good.eq(mpps.pps_good)
        m.d.comb += uart.pps_late.eq(mpps.pps_late)
        m.d.comb += uart.pps_early.eq(mpps.pps_early)

        m.d.comb += synchronizer.pps.eq(mpps.pps)

        m.d.comb += time.mode.eq(uart.timecoder_mode)
        m.d.comb += time.time.eq(uart.time)
        m.d.comb += time.set_time.eq(uart.set_time)
        m.d.comb += time.pps.eq(mpps.pps)
        m.d.comb += time.next_bit.eq(synchronizer.next_code)

        m.d.comb += prn_a.taps.eq(uart.taps_a)
        m.d.comb += prn_b.taps.eq(uart.taps_b)

        m.d.comb += mixer.carrier.eq(oscil.out)
        m.d.comb += mixer.carrier90.eq(oscil.out90)
        m.d.comb += mixer.data.eq(synchronizer.data)
        m.d.comb += mixer.time_code_data.eq(time.data)
        m.d.comb += mixer.mode.eq(uart.mode)

        m.d.comb += self.antena_out.eq(mixer.out)

        return m

if __name__ == '__main__':
    dut = TwstftMain(
            280000,
            70000,
            2500,
            code_len=100,
            uart=None)
    sim = Simulator(dut)
    sim.add_clock(1/280000)

    async def process(ctx: SimulatorContext):
        i = 0
        while True:
            await ctx.tick()
            if i == 10:
                ctx.set(dut.pps, True)
            elif i == 100:
                ctx.set(dut.pps, False)
            i = (i + 1) % 280000

    sim.add_process(process)

    with sim.write_vcd('global_sim.vcd'):
        sim.run_until(4)
