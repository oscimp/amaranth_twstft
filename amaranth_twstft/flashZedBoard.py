#!/usr/bin/env python3

from amaranth import *
from amaranth.build import *
from amaranth_boards.resources import *
from amaranth_twstft.Mixer import *

from amaranth_twstft.zedboard import *

import argparse
import os
import importlib
import subprocess
import sys

#default number of different taps to choose among when dynamically selecting the taps for the LFSR
nb_taps_auto = 32


class TWSTFT_top(Elaboratable):
    """
    A module that generates 70MHz BPSK signal modulated by a n-bits 1PPS-synchronized Pseudo-Random Noise sequence.
    ZedBoard compatible.
    
    Parameters
    ----------
    bit_len : positive integer
        number of bits of the LFSR
    
    noise_len : positive integer
        number of bits that should be generated by the Pseudo-Random Noise Generator befor any reset
        
    taps : non negative integer 
        taps that should be used for the LFSR (set to 0 by default, 0 means the taps are chosen dynamically)
    
    seed : positive integer
        initial state of the LFSR (1 by default)
    
    Attributes
    ----------
    carrier : Signal()
        The signal to be modulated by the PRN
    
    mudulated : Signal()
        the output signal of the module
        the value of the carrier signal modulated by our PRN
    
    _seed : positive integer
        the initial state of the LFSR
        (1 by default)
    
    _noise_len : integer
        the number of PRN bits to generate before the end of 
        the next automatic reset of the LFSR state 
    
    _bit_len : positive integer
        number of bits of the LFSR
    
    """

    def __init__(self, bit_len, noise_len, reload=True, lock_pps_gen=True, taps = 0, seed = 0x1, freqout=2500000,
                 invert_first_code=False, use_uart=True, debug=False):
    
        self.pps_out = Signal()
        self.the_pps_we_love = Signal()
        self.dixmega = Signal()
        self.ref_clk = Signal()

        self._freqout           = freqout
        self._bit_len           = bit_len
        self._noise_len         = noise_len
        self._reload            = reload
        self._lock_pps_gen      = lock_pps_gen
        self._taps              = taps
        self._seed              = seed
        self._invert_first_code = invert_first_code
        self._use_uart          = use_uart
        self._debug             = debug
        
    def elaborate(self,platform):
        m = Module()

        m.domains.sync = ClockDomain()

        uart_pads = None
        
        #parametrizing the platforms outputs
        if (type(platform).__name__ == "ZedBoardPlatform"):
            conna = ("pmoda",0)
            connb = ("pmodb",0)
            connc = ("pmodc",0)
            connd = ("pmodd",0)

            platform.add_resources([
                Resource('external_clk', 0,
                    Subsignal('clk_in', Pins('4',conn=conna, dir='i')),
                    Attrs(IOSTANDARD="LVCMOS33")
                ),
                Resource('pins', 0,
                    Subsignal('clk_out',   Pins('2', conn = connb, dir='o')),
                    Subsignal('output',    Pins('4', conn = connd, dir='o')),
                    Subsignal('enable',    Pins('1', conn = connc, dir='i')),
                    Subsignal('PPS_in',    Pins('4', conn = connc, dir='i')),
                    Subsignal('PPS_out',   Pins('3', conn = connb, dir='o')),
                    Subsignal('PPS_out2',  Pins('1', conn = connb, dir='o')),

                    Subsignal('mixer_o',   Pins('7', conn = connb, dir='o')),
                    Subsignal('mixer2_o',  Pins('8', conn = connb, dir='o')),

                    Subsignal('C2_i',      Pins('2', conn = connc, dir='i')),

                    Subsignal('D1_o',      Pins('1', conn = connd, dir='o')),
                    Subsignal('inv_prn_o', Pins('2', conn = connd, dir='o')), # invert_prn
                    Attrs(IOSTANDARD="LVCMOS33", PULLDOWN="TRUE")
                )
            ])
        elif (type(platform).__name__ == "PynqZ2Platform"):
            connrpi = ("RPI",0)
            platform.add_resources([
                Resource('external_clk', 0,
                    Subsignal('clk_in', Pins('11', conn=connrpi, dir='i')), # RPI-11
                    Attrs(IOSTANDARD="LVCMOS33")
                ),
                Resource('pins', 0,
                    Subsignal('output',    Pins('3',  conn=connrpi, dir='o')), # RPI-3
                    Subsignal('enable',    Pins('8',  conn=connrpi, dir='i')), # RPI-22
                    Subsignal('PPS_in',    Pins('32', conn=connrpi, dir='i')), # RPI-32

                    # debug
                    Subsignal('clk_out',   Pins('15', conn=connrpi, dir='o')), # RPI-15
                    Subsignal('PPS_out',   Pins('36', conn=connrpi, dir='o')), # RPI-36
                    Subsignal('PPS_out2',  Pins('40', conn=connrpi, dir='o')), # RPI-40
                    Subsignal('mixer_o',   Pins('28', conn=connrpi, dir='o')), # RPI-28
                    Subsignal('mixer2_o',  Pins('26', conn=connrpi, dir='o')), # RPI-26
                    Subsignal('inv_prn_o', Pins('24', conn=connrpi, dir='o')), # invert_prn
                    Attrs(IOSTANDARD="LVCMOS33", PULLDOWN="TRUE")
                )
            ])
        elif type(platform).__name__ == "CmodA7_35Platform":
            connect = ("gpio",0)
            platform.add_resources([
                Resource('external_clk', 0,
                    Subsignal('clk_in', Pins('46',conn=connect, dir='i')),
                    Attrs(IOSTANDARD="LVCMOS33")
                ),
                Resource('pins', 0,
                    Subsignal('output',    Pins('31', conn = connect, dir='o')),
                    Subsignal('enable',    Pins('36', conn = connect, dir='i')),
                    Subsignal('PPS_in',    Pins('42', conn = connect, dir='i')),

                    # debug
                    Subsignal('clk_out',   Pins('1',  conn = connect, dir='o')),
                    Subsignal('PPS_out',   Pins('3',  conn = connect, dir='o')),
                    Subsignal('PPS_out2',  Pins('5',  conn = connect, dir='o')),
                    Subsignal('mixer_o',   Pins('7',  conn = connect, dir='o')),
                    Subsignal('mixer2_o',  Pins('9',  conn = connect, dir='o')),
                    Subsignal('inv_prn_o', Pins('11', conn = connect, dir='o')), # invert_prn

                    Attrs(IOSTANDARD="LVCMOS33")
                ),
                # switch mode
                Resource('switch', 0, Pins('23',  conn = connect, dir='i'),
                   Attrs(IOSTANDARD="LVCMOS33")),
               # clean carrier
                Resource('switch', 1, Pins('19',  conn = connect, dir='i'),
                   Attrs(IOSTANDARD="LVCMOS33")),
            ])

            # when first code + counter and use_uart request UART pads
            if self._invert_first_code and self._use_uart:
                uart_pads = platform.request("uart")
        else:
            print("Error: unknown target platform")
            raise Error()

        pins = platform.request('pins',0)

        #allowing to switch between BPSK and QPSK
        clean_carrier = platform.request('switch', 1) # M20
        switch_mode   = platform.request('switch', 0) # F22

        new_clk = platform.request('external_clk',0)

        platform_clk = new_clk.clk_in
        base_clk_freq    = 10000000
        mmcm_clk_out     = Signal()
        mmcm_locked      = Signal()
        mmcm_feedback    = Signal()
    
        clk_input_buf    = Signal()
        m.submodules += Instance("BUFG",
            i_I  = platform_clk.i,
            o_O  = clk_input_buf,
        )
        
        if base_clk_freq == 20000000:
            vco_mult = 42.0
            mmc_out_div = 3.0
        else:
            vco_mult = 63.0
            mmc_out_div = 2.25
        mmc_out_period = 1e9 / (base_clk_freq * vco_mult / mmc_out_div)
                
        m.submodules.mmcm = Instance("MMCME2_ADV",
            p_BANDWIDTH          = "OPTIMIZED",
            p_CLKFBOUT_MULT_F    = vco_mult, 
            p_CLKFBOUT_PHASE     = 0.0,
            p_CLKIN1_PERIOD      = int(1e9 // base_clk_freq), # 20MHz
            
            
            p_CLKOUT0_DIVIDE_F   = mmc_out_div,
            p_CLKOUT0_DUTY_CYCLE = 0.5,
            p_CLKOUT0_PHASE      = 0.0,

            p_SS_EN              = "FALSE",
            
            i_DADDR                = Const(0, 7),
            i_DEN                  = 0,
            i_DI                   = Const(0, 16),
            i_DWE                  = 0,

            i_PSEN                 = 0,
    
            i_PWRDWN               = 0,
            i_RST                  = 0,
            i_CLKINSEL             = 1,
            i_CLKFBIN              = mmcm_feedback,
            o_CLKFBOUT             = mmcm_feedback,
            i_CLKIN1               = clk_input_buf,
            i_CLKIN2               = Const(0),
            o_CLKOUT0              = mmcm_clk_out,
            o_LOCKED               = mmcm_locked,
        )
    
        m.submodules += Instance("BUFG",
            i_I  = mmcm_clk_out,
            o_O  = ClockSignal("sync"),
        )
        m.d.comb += ResetSignal("sync").eq(~mmcm_locked)
    
        clock_freq = 1e9/mmc_out_period
        platform.add_clock_constraint(clk_input_buf, base_clk_freq)
        print(f"clock freq {clock_freq} mmc out period {mmc_out_period}")

        self.mixer = Mixer(self._bit_len, self._noise_len, self._reload,
                           self._lock_pps_gen, self._taps, self._seed,
                           clock_freq,
                           self._freqout,
                           self._invert_first_code,
                           uart_pads = uart_pads,
                           debug     = self._debug)
        m.submodules.mixer = mixer = self.mixer

        m.d.comb += [
            mixer.pps_in.eq(pins.PPS_in.i),
            mixer.switch_mode.eq(switch_mode.i),
            mixer.global_enable.eq(pins.enable.i),
            mixer.output_carrier.eq(clean_carrier.i),
        ]

        m.d.sync+=[
            pins.output.o.eq(mixer.mod_out), # JMF 240612
        ]

        if self._debug:
            m.d.sync += [
                pins.clk_out.o.eq(mixer.dixmega),
                pins.PPS_out.o.eq(mixer.pps_out),   # test
                pins.PPS_out2.o.eq(mixer.the_pps_we_love),
                pins.mixer_o.o.eq(mixer.output),
                pins.mixer2_o.o.eq(mixer.output2),
                pins.inv_prn_o.o.eq(mixer.invert_prn_o),
            ]
        return m

def platform_get(platform_name):
    plt_name_l = platform_name.lower()
    if plt_name_l.startswith("zedboard"):
        target = "amaranth_twstft.zedboard:ZedBoardPlatform"
    elif plt_name_l.startswith("cmoda7"):
        target = "amaranth_boards.cmod_a7:CmodA7_35Platform"
    elif plt_name_l.startswith("pynq"):
        target = "amaranth_twstft.pynq_z2:PynqZ2Platform"
    else:
        return None

    tgt = target.split(':')
    if len(tgt) != 2:
        print("wrong platform name must be zedboard, cmoda7, pynqz2")
        return None
    (module, name) = tgt
    platform_module = importlib.import_module(module)

    # Once we have the relevant module, extract our class from it.
    platform_class = getattr(platform_module, name)
    return platform_class

# update SPI flash (cmod A7 only)
def flashBistream(build_dir="build"):
    tool = os.environ.get("OPENFPGALOADER", "openFPGALoader")
    bit_name = os.path.join(build_dir, "top.bit")
    subprocess.check_call([tool, "-b", "cmoda7_35t", '-f', '--freq', '30e6', '-m', bit_name])

#flasher le programme sur la carte SD manuellement :
#- brancher la carte microsd dans l'ordi avec l'adaptateur
#- flasher le programme en question
#- bash : 
#	bootgen -w -image toto.bif -arch zynq -process_bitstream bin
#	mount /mnt/removable
#	cp build/top.bit.bin / mnt/removable/system.bit.bin
#	umount /mnt/removable

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform",     default="zedboard", help="Target Platform (pynq, cmoda7, zedboard(default)", type=str)
    parser.add_argument("--bitlen",       default=17,help="number of bits of the LFSR", type=int)
    parser.add_argument("--noiselen",     default=100000,  help="length of the PRN sequence", type=float)
    parser.add_argument("--no-reload",    help="stop generation after noiselen bits", action="store_true")
    parser.add_argument("-s","--seed",    default=1, help="initial value of the LFSR (default 1)", type=int)
    parser.add_argument("-t","--taps",    help="taps positions for the LFSR (if not defined, allows to dynamically define taps (currently not supported so default taps will be the smallest msequence generator taps))", type=int)
    parser.add_argument("-m","--modfreq", default=int(2.5e6), help="frequency of the PSK modulation (Herz) (default :2.5e6)", type=int)
    parser.add_argument("--invert-first-code",    help="deprecated: default behaviour. Use --no-invert-first-code to disable xoring + counter", action="store_true")
    parser.add_argument("--no-invert-first-code", help="disable invert (xor) the first code after PPS rise and 8bits counter", action="store_true")
    parser.add_argument("--no-uart",      help="disable uart request for PC second sent during sequence 1 -> 9 (cmoda7 only", action="store_true")
    parser.add_argument("-p","--print",   help="creates a binary file containing the PRN sequence that should be generated", action="store_true")
    parser.add_argument("-v","--verbose", help="prints all the parameters used for this instance of the program", action="store_true")
    parser.add_argument("--no-build",     help="sources generate only", action="store_true")
    parser.add_argument("--no-load",      help="don't load bitstream", action="store_true")
    parser.add_argument("--flash",        help="write bitstream into SPI flash (cmoda7 only)", action="store_true")
    parser.add_argument("--build-dir",    default="build", help="build directory")
    parser.add_argument("--conv-to-bin",  help="convert .bit file to .bit.bin", action="store_true")
    parser.add_argument("--debug",        help="enable test signals", action="store_true")
    parser.add_argument("--toolchain",    default="Vivado", help="toolchain to use (Vivado or Symbiflow) (cmoda7 only) (default: Vivado)")
    args = parser.parse_args()

    if args.invert_first_code:
        print("--invert-first-code is deprecated (default behaviour)")

    if args.conv_to_bin:
        build_dir=args.build_dir
        name = "top"
        input_bit  = build_dir + "/" + name + ".bit"
        output_bit = input_bit + ".bin"
        if exists(output_bit):
            os.remove(output_bit)
        with open(name + ".bif", "w") as fd:
            fd.write("all:\n")
            fd.write("{\n")
            fd.write(f"\t{input_bit}\n")
            fd.write("}\n")
        subprocess.check_call(["bootgen", "-w", "-image", name + ".bif", "-arch", "zynq", "-process_bitstream", "bin"])
        os.remove(name + ".bif")
        sys.exit(0)

    if args.taps :
        t = args.taps
    else:
        try:
            t = get_taps(args.bitlen)[0]
        except:
            taps_autofill(args.bitlen,32)
            t = get_taps(args.bitlen)[0]

    if args.print :
        write_prn_seq(args.bitlen, t, args.seed, seqlen=int(args.noiselen))

    invert_first_code = not args.no_invert_first_code
    if invert_first_code and int(args.noiselen) >= int(args.modfreq):
        invert_first_code = False
        print(f"First code invertion disabled: noiselen ({args.noiselen}) >= modfreq ({args.modfreq})")

    if not args.platform == "cmoda7" and args.toolchain == "Symbiflow":
        print("Error: zynq based boards are untested with Symbiflow toolchain")
        print("\tSymbiflow may only used with cmoda7 board")
        sys.exit(1)

    if args.verbose:
        print("bit length of the LFSR : "+str(args.bitlen))
        print("number of bits generated per pps signal received : "+ str(args.noiselen))
        print("baseband signal frequency : "+str(args.modfreq))
        print("seed : "+str(args.seed))
        print("taps : "+ str(t))
        print("First code xoring + 8 bit counter: " + ("Enabled" if invert_first_code else "Disabled"))

    flash_bitstream = True if args.platform == "cmoda7" and args.flash else False

    platform = platform_get(args.platform)
    if platform is None:
        print("error: undifined/unknown platform")
        sys.exit(1)

    print(platform)

    gateware = platform(toolchain=args.toolchain).build(
        TWSTFT_top(args.bitlen, int(args.noiselen), reload=not args.no_reload,
                   taps=t, seed=args.seed,
                   freqout=args.modfreq, invert_first_code=invert_first_code,
                   use_uart=not args.no_uart, debug=args.debug),
        do_program=not (args.no_load or flash_bitstream), do_build=not args.no_build, build_dir=args.build_dir)
    if flash_bitstream:
        flashBistream(args.build_dir)

    # if no build nothing produces -> force
    if args.no_build:
        gateware.execute_local(args.build_dir, run_script=False)
