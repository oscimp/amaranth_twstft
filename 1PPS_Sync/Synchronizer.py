#!/usr/bin/env python3

from amaranth import *
from Prescaler import *
from PRN import *
from amaranth.sim import *
import argparse

class Synchronizer(Elaboratable):
	"""A module that generates a 20-bits PRN synchronized with a 1-PPS Signal in input
    Parameters
    ----------
    freqin : positive integer
		the frequency of the clock used by the fpga
	
	freqout : positive integer
		frequency we want to use to set the cadence of our PRN generation
    Attributes
    ----------
	output : Signal()
		the output of the module
		it equals the PRN when a 1-PPS Signal has been 
		received within the last second (defined by the fpga's clock domain)
		Else, it equals 0 
	pps : Signal()
		the 1-PPS signal transmitted by the precise frequency source
	
	freqin : integer
		the frequency of the fpga's clock
	
	freqout : integer
		the frequency of our PRN Generation
    """

	def __init__(self, freqin, freqout, noise_len = pow(2,20)-1, taps=0, seed = 0xFFFFF):
		self.pps = Signal(name="sync_pps_input")
		self.output = Signal(name="sync_output")
		
		if taps == 0:
			self.dynamic_taps = True
			self.tsel = Signal(5, name="taps_selector_sync")
		else :
			self.dynamic_taps = False
			self.taps = taps
			
		self.seed = seed
		self._freqin = freqin
		self._freqout = freqout
		self.noise_len = noise_len
	
	def elaborate(self, platform):
		m = Module()

		cnt = Signal(32, name="sync_counter")
		old_pps = Signal(name="sync_last_clk_pps")
		m.d.sync += old_pps.eq(self.pps)
		
		if self.dynamic_taps :
			m.submodules.prn = prn = PrnGenerator(seed = self.seed)
			m.d.comb += prn.tsel.eq(self.tsel)
		else :
			m.submodules.prn = prn = PrnGenerator(taps=self.taps, seed=self.seed)
		
		m.submodules.presc = presc = Prescaler(self._freqin, self._freqout)

		m.d.comb += [
			prn.next.eq(presc.output),
			self.output.eq(prn.output)
		]
		
		rise = Signal()
		m.d.comb += rise.eq((old_pps ^ self.pps) & self.pps)
		


		
		with m.If(cnt<self.noise_len) :
			with m.If(presc.output):
				m.d.sync += cnt.eq(cnt+1)
			m.d.comb += [
				presc.enable.eq(1),
				prn.enable.eq(1)
			]
		with m.Else():
			m.d.comb += [
				presc.enable.eq(0),
				prn.enable.eq(0)
			]

		with m.If(rise):
			m.d.sync += cnt.eq(0)
		return m


#run "python3 {thisfile}" to start this simulation
#You can use GTKWave to visualize the result of the simulation below 
#and check if the architecture defined above is correct
#(it doesn't mean you won't have any trouble whe flashing on your FPGA as each board may have its own limits)
if __name__ == "__main__" :
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--noiselen", help="length of the PRN sequence", type=int)
	parser.add_argument("--seed", help="initial value of the LFSR", type=int)
	parser.add_argument("--taps", help="taps positions for the LFSR", type=int)
	args = parser.parse_args()
	if args.noiselen :
		n = args.noiselen
	else :
		n = 0
	if args.seed:
		s = args.seed
	else :
		s = 0xFFFFF
	if args.taps :
		t = args.taps
	else:
		t = 0
	
	#10 MHz Clock, 2.5 MHz prn, static taps, noise_len = 2²⁰-1
	dut = Synchronizer(100000,25000, seed = s, taps = t, noise_len=n)
	sim = Simulator(dut)
	
	def proc():
		
		#2 seconds before the first pps
		for i in range(200000):
			yield Tick()
		print("2 sec")
		
		#simulating a pps
		yield dut.pps.eq(1)
		yield Tick()
		yield dut.pps.eq(0)
		
		#waiting 1 second (
		for i in range(100000):
			yield Tick()
		print("3 sec")
		#simulating an interrupted pps 
		yield dut.pps.eq(1)
		yield Tick()
		yield dut.pps.eq(0)
		for i in range(50000):
			yield Tick()
		print("3.5 sec")
		yield dut.pps.eq(1)
		yield Tick()
		yield dut.pps.eq(0)
		for i in range(100000):
			yield Tick()
		print("4.5 sec")
		#simulating a regular pps
		for j in range(3):
			yield dut.pps.eq(1)
			yield Tick()
			yield dut.pps.eq(0)
			for i in range(100000):
				yield Tick()
			
	sim.add_clock(1e-5)
	sim.add_process(proc)
	with sim.write_vcd("test.vcd"):
		sim.run()
