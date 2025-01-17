from amaranth import Module, Shape, Signal
from amaranth.lib.wiring import Component, In, Out

from synchronizer import Synchronizer 
from mixer import Mixer, Mode
from oscillator import Oscillator
from pps_detection import PPSDetector
from prn import PrnGenerator


class TwstftMain(Component):
    pps: In(1)
    antena_out: Out(1)

    def __init__(self, f_clock, f_carrier, f_code, code_len=10**4, mode=Mode.BPSK, bit_len=14, taps=43, seed=1):
        super().__init__()
        self.f_clock = f_clock
        self.f_carrier = f_carrier
        self.f_code = f_code
        assert f_clock % f_carrier == 0
        assert f_carrier % f_code == 0
        self.code_len = code_len
        self.mode = mode
        self.bit_len = bit_len
        self.taps = taps
        self.seed = seed

    def elaborate(self, platform):
        m = Module()

        # Config
        mode = Signal(Shape.cast(Mode))
        taps = Signal(self.bit_len)
        seed = Signal(self.bit_len)
        
        m.d.comb += mode.eq(self.mode)
        m.d.comb += taps.eq(self.taps)
        m.d.comb += seed.eq(self.seed)

        # Modules
        m.submodules.pps = mpps = PPSDetector()
        m.submodules.prn = prn = PrnGenerator(self.bit_len)
        m.submodules.oscil = oscil = Oscillator(self.f_clock, self.f_carrier)
        m.submodules.synchronizer = synchronizer = Synchronizer(
                prn,
                self.code_len,
                self.f_clock // self.f_code,
                oscil)
        m.submodules.mixer = mixer = Mixer()

        # Connexions

        m.d.comb += mpps.pps_in.eq(self.pps)

        m.d.comb += synchronizer.pps.eq(mpps.pps)
        m.d.comb += synchronizer.mode.eq(mode)

        m.d.comb += prn.taps.eq(taps)
        m.d.comb += prn.seed.eq(seed)

        m.d.comb += mixer.carrier.eq(oscil.out)
        m.d.comb += mixer.carrier90.eq(oscil.out90)
        m.d.comb += mixer.data.eq(synchronizer.data)
        m.d.comb += mixer.mode.eq(mode)

        m.d.comb += self.antena_out.eq(mixer.out)

        return m
