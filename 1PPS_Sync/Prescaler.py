from math import ceil
from amaranth import *
from amaranth.sim import *

class Prescaler(Elaboratable):
	"""A prescaler implementation to demultiply the clock signal

    Parameters
    ----------
    freqin : int or float
        the frequency we intend to  use in our FPGA
        
    freqout :non zero int or float
        the frequency of the output signal rising edge

    Attributes
    ----------
	output : Signal()

    _ticks_per_period : int
		number of clock ticks between each output rising edge
    _cnt : Signal(32)
		number of ticks waited sinc the last output rising edge
	enable : Signal() 
		input signal that should be set to 0 if we want to force the prescaler 
		to wait in its initial state, to one if we want to read its output
    """

	def __init__(self,freqin,freqout):
		self._ticks_per_period = ceil(freqin/freqout)
		self.cnt = Signal(32, reset=0,name="presc_counter")
		self.output = Signal(1, reset=0,name="presc_output")
		self.enable = Signal(1,reset=1,name="presc_enable")
	
	def elaborate(self, platform):
		m = Module()
		
		with m.If(self.cnt == 0):
			m.d.sync += self.output.eq(1)
		with m.Else():
			m.d.sync += self.output.eq(0)
		
		m.d.sync += self.cnt.eq(self.cnt +1)
		
		with m.If (~self.enable):
			m.d.sync += [
				self.cnt.eq(0),
				self.output.eq(0)
			]
		with m.If(self.cnt==self._ticks_per_period-1):
			m.d.sync+=[
				self.cnt.eq(0),
			]
		
		return m


if __name__ == "__main__":
	freqin = 10e6
	dut = Prescaler(freqin,2.5e6)
	sim = Simulator(dut)
	
	def proc():
		#test for the normal use of the prescaler
		for i in range(200):
			yield Tick()
		
		#test for the stop of the output signal whil ~enable
		yield dut.enable.eq(0)
		for i in range(100):
			yield Tick()
		
		#test for the return of the normal use of the prescaler
		yield dut.enable.eq(1)
		for i in range(200):
			yield Tick()

	sim.add_clock(1/freqin)
	sim.add_sync_process(proc)
	with sim.write_vcd("test.vcd"):
		sim.run()
