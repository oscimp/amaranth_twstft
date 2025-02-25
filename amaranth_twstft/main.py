from amaranth import ClockDomain, Module, Shape, Signal
from amaranth.lib.wiring import Component, In, Out
from amaranth.sim import Simulator, SimulatorContext
from amaranth_boards.resources import *

from amaranth_twstft.calibration_output import CalibrationOutput
from amaranth_twstft.clocking import Clocking
from amaranth_twstft.common import CalibrationMode
from amaranth_twstft.time_coder import TimeCoder
from amaranth_twstft.uart_wrapper import UARTWrapper
from amaranth_twstft.synchronizer import Synchronizer
from amaranth_twstft.mixer import Mixer, Mode
from amaranth_twstft.oscillator import Oscillator
from amaranth_twstft.prn import PrnGenerator


class TwstftMain(Component):
    clk10_in: In(1)
    pps: In(1)
    antena_out: Out(1)
    calib_out: Out(1)
    reset: In(1)

    def __init__(
            self,
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
        self.f_clock = int(280e6)
        self.f_carrier = f_carrier
        self.f_code = f_code
        assert self.f_clock % f_carrier == 0
        assert f_carrier % f_code == 0
        self.code_len = code_len
        self.bit_len = bit_len
        self.uart = uart

    def elaborate(self, platform):
        m = Module()

        # Modules
        m.domains.sync = ClockDomain()

        m.submodules.clocking = clocking = Clocking()
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
        m.submodules.calib = calib = CalibrationOutput()


        # Connexions

        m.d.comb += clocking.clk10_in.eq(self.clk10_in)
        m.d.comb += clocking.pps_in.eq(self.pps)
        m.d.comb += clocking.reset.eq(self.reset)
        m.d.comb += clocking.auto_calibrate.eq(uart.calib_mode == CalibrationMode.AUTO)
        m.d.comb += clocking.ask_calibrate.eq(uart.ask_calib)

        m.d.comb += uart.pps_good.eq(clocking.pps_good)
        m.d.comb += uart.pps_late.eq(clocking.pps_late)
        m.d.comb += uart.pps_early.eq(clocking.pps_early)
        m.d.comb += uart.code_unaligned.eq(synchronizer.code_unaligned)
        m.d.comb += uart.symbol_unaligned.eq(synchronizer.oscil_unaligned)
        m.d.comb += uart.oscil_unaligned.eq(synchronizer.oscil_unaligned)
        m.d.comb += uart.calibration_finish.eq(clocking.calibration_finish)
        m.d.comb += uart.pps_phase.eq(clocking.pps_phase)

        m.d.comb += synchronizer.pps.eq(clocking.pps)

        m.d.comb += time.mode.eq(uart.timecoder_mode)
        m.d.comb += time.time.eq(uart.time)
        m.d.comb += time.set_time.eq(uart.set_time)
        m.d.comb += time.pps.eq(clocking.pps)
        m.d.comb += time.next_bit.eq(synchronizer.next_code)

        m.d.comb += prn_a.taps.eq(uart.taps_a)
        m.d.comb += prn_b.taps.eq(uart.taps_b)

        m.d.comb += mixer.carrier.eq(oscil.out)
        m.d.comb += mixer.carrier90.eq(oscil.out90)
        m.d.comb += mixer.data.eq(synchronizer.data)
        m.d.comb += mixer.time_code_data.eq(time.data)
        m.d.comb += mixer.mode.eq(uart.mode)

        m.d.comb += calib.mode.eq(uart.calib_mode)
        m.d.comb += calib.pps.eq(clocking.pps)
        m.d.comb += calib.delayed_pps.eq(clocking.delayed_pps)

        m.d.sync += self.antena_out.eq(mixer.out)
        m.d.comb += self.calib_out.eq(calib.out)

        return m

if __name__ == '__main__':
    dut = TwstftMain(
            70000,
            2500,
            code_len=100,
            uart=None)
    sim = Simulator(dut)
    sim.add_clock(1/280000, phase=0, domain='sync')
    sim.add_clock(1/210000, phase=0, domain='clk210')
    sim.add_clock(1/10000, phase=1/2/280000, domain='clk10')

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
