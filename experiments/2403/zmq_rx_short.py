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
from gnuradio import zeromq




class zmq_rx_short(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 5e6
        self.duration_in_s = duration_in_s = 3600

        ##################################################
        # Blocks
        ##################################################

        self.zeromq_sub_source_0 = zeromq.sub_source(gr.sizeof_short, 1, 'tcp://127.0.0.1:5555', 100, False, (-1), '', False)
        self.blocks_head_0 = blocks.head(gr.sizeof_short*1, (int(samp_rate*duration_in_s*2*2)))
        self.blocks_file_sink_0_0 = blocks.file_sink(gr.sizeof_short*1, '/data/test.bin', False)
        self.blocks_file_sink_0_0.set_unbuffered(False)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_head_0, 0), (self.blocks_file_sink_0_0, 0))
        self.connect((self.zeromq_sub_source_0, 0), (self.blocks_head_0, 0))


    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_head_0.set_length((int(self.samp_rate*self.duration_in_s*2*2)))

    def get_duration_in_s(self):
        return self.duration_in_s

    def set_duration_in_s(self, duration_in_s):
        self.duration_in_s = duration_in_s
        self.blocks_head_0.set_length((int(self.samp_rate*self.duration_in_s*2*2)))




def main(top_block_cls=zmq_rx_short, options=None):
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
