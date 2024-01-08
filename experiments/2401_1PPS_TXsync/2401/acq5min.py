#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# GNU Radio version: 3.10.7.0

from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import uhd
import time




class x310_twstft(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 5e6

        ##################################################
        # Blocks
        ##################################################

        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(("addr0=192.168.10.2", "")),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,2)),
            ),
        )
        self.uhd_usrp_source_0.set_clock_source('external', 0)
        self.uhd_usrp_source_0.set_time_source('external', 0)
        self.uhd_usrp_source_0.set_subdev_spec('A:0 B:0', 0)
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_time_unknown_pps(uhd.time_spec(0))

        self.uhd_usrp_source_0.set_center_freq(70e6, 0)
        self.uhd_usrp_source_0.set_antenna('A', 0)
        self.uhd_usrp_source_0.set_gain(6, 0)

        self.uhd_usrp_source_0.set_center_freq(70e6, 1)
        self.uhd_usrp_source_0.set_antenna('A', 1)
        self.uhd_usrp_source_0.set_gain(0, 1)

        self.uhd_usrp_source_0.set_start_time(uhd.time_spec(5))
        self.blocks_interleave_0 = blocks.interleave(gr.sizeof_gr_complex*1, 1)
        self.blocks_head_0 = blocks.head(gr.sizeof_gr_complex*1, (int(samp_rate*60*5*2)))
        self.blocks_file_sink_0_0 = blocks.file_sink(gr.sizeof_short*1, '/data/fichier.bin', False)
        self.blocks_file_sink_0_0.set_unbuffered(False)
        self.blocks_complex_to_interleaved_short_0_0 = blocks.complex_to_interleaved_short(False,32767)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_complex_to_interleaved_short_0_0, 0), (self.blocks_file_sink_0_0, 0))
        self.connect((self.blocks_head_0, 0), (self.blocks_complex_to_interleaved_short_0_0, 0))
        self.connect((self.blocks_interleave_0, 0), (self.blocks_head_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_interleave_0, 0))
        self.connect((self.uhd_usrp_source_0, 1), (self.blocks_interleave_0, 1))


    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_head_0.set_length((int(self.samp_rate*60*5*2)))
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)




def main(top_block_cls=x310_twstft, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    tb.wait()


if __name__ == '__main__':
    main()
