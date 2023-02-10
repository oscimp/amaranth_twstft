#!/usr/bin/env python3

import os
import subprocess
from os.path import exists
from amaranth.build import *
from amaranth.vendor.xilinx import *
from amaranth_boards.resources import *

__all__ = ["PynqZ2Platform"]

class PynqZ2Platform(XilinxPlatform):
    device = "xc7z020"
    package = "clg400"
    speed = "1"
    default_clk = "clk125"
    resources = [
        Resource("clk125", 0, Pins("H16", dir="i"),
                 Clock(125e6), Attrs(IOSTANDARD="LVCMOS33")),

        *SwitchResources(
            pins="M20 M19",
            attrs=Attrs(IOSTANDARD="LVCMOS33")),

        *ButtonResources(
            pins="D19 D20 L20 L19",
            attrs=Attrs(IOSTANDARD="LVCMOS33")),

        *LEDResources(
            pins="R14 P14 N16 M14",
            attrs=Attrs(IOSTANDARD="LVCMOS33")),

        RGBLEDResource(0,
            r="N15", g="G17", b="L15",                          # LD4
            attrs=Attrs(IOSTANDARD="LVCMOS33")),
        RGBLEDResource(1,                                       # LD5
            r="M15", g="L14", b="G14",
            attrs=Attrs(IOSTANDARD="LVCMOS33")),

        Resource("hdmi_rx", 0,                                  # J10
            Subsignal("cec", Pins("H17", dir="io")),
            Subsignal("clk", DiffPairs("N18", "P19", dir="i"),
                Attrs(IOSTANDARD="TMDS_33")),
            Subsignal("d",   DiffPairs("V20 T20 N20", "W20 U20 P20", dir="i"),
                Attrs(IOSTANDARD="TMDS_33")),
            Subsignal("hpd", Pins("T19", dir="o")),
            Subsignal("scl", Pins("U14", dir="io")),
            Subsignal("sda", Pins("U15", dir="io")),
            Attrs(IOSTANDARD="LVCMOS33")),

        Resource("hdmi_tx", 0,                                  # J11
            Subsignal("cec", Pins("G15", dir="io")),
            Subsignal("clk", DiffPairs("L16", "L17", dir="o"),
                Attrs(IOSTANDARD="TMDS_33")),
            Subsignal("d",   DiffPairs("K17 K19 J18", "K18 J19 H18", dir="o"),
                Attrs(IOSTANDARD="TMDS_33")),
            Subsignal("hpd", PinsN("R19", dir="i")),
            Subsignal("scl", Pins("B9", dir="io")),
            Subsignal("sda", Pins("B13", dir="io")),
            Attrs(IOSTANDARD="LVCMOS33"))

    ]
    connectors = [
        Connector("pmoda", 0, "Y18 Y19 Y16 Y17 - - U18 U19 W18 W19 - -"),
        Connector("pmodb", 0, "W14 Y14 T11 T10 - - V16 W16 V12 W13 - -"),
        # arduino 
        # AR_J3                AR8 AR9 AR10 AR11 AR12 AR13 GND A   AR_SDA AR_SCL
        Connector("AR_J3", 0, "V17 V18 T16  R17  P18  N17  -   Y13 P16    P15"),
        # AR_J4                AR0 AR1 AR2 AR3 AR4 AR5 AR6 AR7
        Connector("AR_J4", 0, "T14 U12 U13 V13 V15 T15 R16 U17"),
        # AR_SPI               AR_MISO 3V3 AR_SCK AR_MOSI AR_SS GND
        Connector("AR_J7", 0, "W15     -   H15    T12     F16   -"),
        # AR_J1 (analog)       A5  A4  A3  A2  A1  A0
        Connector("AR_J1", 0, "U10 T5  V11 W11 Y12 Y11"),
        # XADC TODO
        # Raspberry Pi
        Connector("RPI", 0, "- - W18 - W19 - V6 Y18 - Y19 U7 C20 V7 - U8 W6 - U18 V8 - V10 U19 W10 F19 - F20 Y16 Y17 Y6 - Y7 B20 W8 - Y8 B19 W9 A20 - Y9"), 
    ]

    def toolchain_program(self, products, name, **kwargs):
        tool = os.environ.get("OPENFPGALOADER", "openFPGALoader")
        with products.extract("{}.bit".format(name)) as bitstream_filename:
            print(bitstream_filename)
            print(os.getcwd())
            print(name)
            subprocess.check_call([tool, "-b", "pynq_z2", '--freq', '30e6', '-m', bitstream_filename])
            if exists(bitstream_filename + ".bin"): 
            	os.remove(bitstream_filename + ".bin")
            with open(name+".bif", "w") as fd:
                fd.write("all:\n")
                fd.write("{\n")
                fd.write(f"\t{bitstream_filename}\n")
                fd.write("}\n")
            subprocess.check_call(["bootgen", "-w", "-image", name + ".bif", "-arch", "zynq", "-process_bitstream", "bin"])
            os.remove(name+".bif")
    

