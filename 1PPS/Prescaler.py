from math import ceil
from amaranth import *

class Prescaler(Elaboratable):
    # freqin should be set to the frequency of the board's clock
    # freqout is the frequency you want to obtain on the output of the module
	def __init__(self,freqin,freqout):
		self.ticks_per_period = ceil(freqin/freqout)
		self.cnt = Signal(32, reset=0)
		self.output = Signal(1, reset=0)
	
	def elaborate(self, platform):
		m = Module()
		
		m.d.sync += [
			self.cnt.eq(self.cnt +1),
			self.output.eq(0)
		]
		
		with m.If(self.cnt==self.ticks_per_period-1):
			m.d.sync+=[
				self.cnt.eq(0),
				self.output.eq(1)
			]
		
		return m