from amaranth import *
from Prescaler import *
from Sync_PRN import *
from amaranth.sim import *

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

	def __init__(self, freqin, freqout):
		self.pps = Signal(name="sync_pps_input")
		self.output = Signal(name="sync_output")
		self._freqin = freqin
		self._freqout = freqout
	
	def elaborate(self, platform):
		m = Module()

		debug = Signal()
		cnt = Signal(32, name="sync_counter")
		old_pps = Signal(name="sync_last_clk_pps")

		m.submodules.prn = prn = PrnGenerator()
		m.submodules.presc = presc = Prescaler(self._freqin, self._freqout)

		m.d.comb += prn.enable.eq(presc.output)
		m.d.comb += debug.eq((old_pps ^ self.pps) & self.pps)

		m.d.sync += old_pps.eq(self.pps)

		with m.If( (old_pps ^ self.pps) & self.pps ):
			m.d.sync += [
				cnt.eq(cnt.reset),
				prn.reset.eq(1),
				presc.enable.eq(0)
			]
		with m.Else():
			m.d.sync += [
				prn.reset.eq(0),
				presc.enable.eq(1)
			]
			
			with m.If(cnt<self._freqin):
				m.d.comb += self.output.eq(prn.output)
				m.d.sync += cnt.eq(cnt+1)
			with m.Else():
				m.d.comb += self.output.eq(0)
				m.d.sync += cnt.eq(cnt)
		
		return m

if __name__ == "__main__" :
	
	dut = Synchronizer(1000,800)
	sim = Simulator(dut)
	def proc():
		#making sure the PRN doesn't emit before we receive a pps
		for i in range(2000) :
			yield Tick()

		#starting to emit a pps every second
		for i in range(10000) :
			yield Tick()
			if (i%1000==0):
				yield dut.pps.eq(1)
			else :
				yield dut.pps.eq(0)
		
		#starting to emit a pps every second + few seconds us
		#(to make sure we stop emiting a prn after what we consider a second)
		for i in range(10000) :
			yield Tick()
			if (i%1050==0):
				yield dut.pps.eq(1)
			else :
				yield dut.pps.eq(0)

		#starting to emit a pps every second - few us 
		#(to make sure we restart emiting a prn even though we didn't finish our sequence)
		for i in range(10000) :
			yield Tick()
			if (i%950==0):
				yield dut.pps.eq(1)
			else :
				yield dut.pps.eq(0)

	sim.add_clock(1e-3)
	sim.add_process(proc)
	with sim.write_vcd("test.vcd"):
		sim.run()