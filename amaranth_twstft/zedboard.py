#!/usr/bin/env python3

import os
import subprocess
from os.path import exists
from amaranth.build import *
# from amaranth.vendor.xilinx import *
from amaranth.vendor import *
from amaranth_boards.resources import *

__all__ = ["ZedBoardPlatform"]

class ZedBoardPlatform(XilinxPlatform):
    device = "xc7z020"
    package = "clg484"
    speed = "1"
    default_clk = "clk100"
    resources = [
        Resource("clk100", 0, Pins("Y9", dir="i"),
                 Clock(100e6), Attrs(IOSTANDARD="LVCMOS33")),

        Resource("userclk", 0, Pins("AA9", dir="i"), # pmoda.4
                 Clock(20e6), Attrs(IOSTANDARD="LVCMOS33")),

        *SwitchResources(
            pins="F22 G22 H22 F21 H19 H18 H17 M15",
            attrs=Attrs(IOSTANDARD="LVCMOS18", PULLDOWN="TRUE")),

        *ButtonResources(
            pins="P16 R16 N15 R18 T18",
            attrs=Attrs(IOSTANDARD="LVCMOS18")),

        *LEDResources(
            pins="T22 T21 U22 U21 V22 W22 U19 U14",
            attrs=Attrs(IOSTANDARD="LVCMOS33")),
    ]
    connectors = [
        Connector("pmoda", 0, "Y11 AA11 Y10 AA9 - - AB11 AB10 AB9 AA8 - -"),
        Connector("pmodb", 0, "W12 W11  V10 W8  - - V12  W10  V9  V8  - -"),
        Connector("pmodc", 0, "AB7 AB6  Y4  AA4 - - R6   T6   T4  U4  - -"),
        Connector("pmodd", 0, "V7  W7   V5  V4  - - W6   W5   U6  U5  - -"),
    ]

    def toolchain_program(self, products, name, **kwargs):
        tool = os.environ.get("OPENFPGALOADER", "openFPGALoader")
        with products.extract("{}.bit".format(name)) as bitstream_filename:
            print(bitstream_filename)
            print(os.getcwd())
            print(name)
            subprocess.check_call([tool, "-b", "zedboard", '--freq', '30e6', '-m', bitstream_filename])
            if exists(bitstream_filename + ".bin"): 
            	os.remove(bitstream_filename + ".bin")
            with open(name+".bif", "w") as fd:
                fd.write("all:\n")
                fd.write("{\n")
                fd.write(f"\t{bitstream_filename}\n")
                fd.write("}\n")
            subprocess.check_call(["bootgen", "-w", "-image", name + ".bif", "-arch", "zynq", "-process_bitstream", "bin"])
            os.remove(name+".bif")
    

