#!/usr/bin/env python3

from amaranth import *
from amaranth.sim import *
from math import log, ceil



class PrnGenerator(Elaboratable):
    
	def __init__(self,bit_len,taps,seed):
		
		self._taps = Signal(bit_len, reset = taps, name="prn_used_taps")

		self.shift = Signal()
		self.reg = Signal(bit_len, reset = seed)
		self.output = Signal()
	
	def elaborate(self,platform):
		m = Module()

		insert = Signal()
		
		m.d.comb += [
			insert.eq((self._taps & self.reg).xor()),
			self.output.eq(self.reg[0]),
		]

		with m.If(self.shift):
			m.d.sync += [
				self.reg.eq(Cat(self.reg[1:],insert)),
			]
			
		return m



class Connector(Elaboratable):
    
    def elaborate(self,platform):
        
        m = Module()
        m.submodules.prn = prn = PrnGenerator(8,43,1)
		
		if platform is not None:
			if (platform.device =="iCE40UP5K"):
			
			    m.domains.sync = ClockDomain(reset_less = True)
			    platform.lookup(platform.default_clk).attrs['GLOBAL'] = False
			    
			    input_clk = platform.request("clk12",0)
			    
			    locked = Signal()
			    pllout = Signal()
			    divf = 66
			    divq = 3
			    
			    m.submodules.pll = Intance("SB_PLL40_PAD",
			        p_FEEDBACK_PATH = "SIMPLE",
			        p_DIVR = 0,
			        p_DIVF = divf,
			        p_DIVQ = divq,
			        p_FILTER_RANGE = 1,
			        
			        o_LOCK = locked,
			        i_RESETB = 1,
			        i_BYPASS = 0,
			        i_PACKAGEPIN = input_clk,
			        o_PLLOUTCORE = pllout
			    )
			    
			    m.d.comb += ClockSignal("sync").eq(pllout)
			    clkrate = (platform.default_clk_frequency * (1+divf))/pow(2,divq)
			
				conn = ('j', 1)
				platform.add_resources([
					Resource('lfsr', 0,
						Subsignal('prn', Pins('7', conn = conn, dir='o')),
						Subsignal('clk', Pins('11', conn = conn, dir='o')),
						Subsignal('enable', Pins('15', conn = conn, dir='i')),
						Attrs(IO_STANDARD="SB_LVCMOS")
					)
				])
				
			m.submodules.presc = presc = Prescaler(clkrate, 2.5e6)
				
			interface = platform.request('lfsr',0)
				
			m.d.comb += [
			    interface.prn.eq(prn.output),
			    interface.clk.eq(ClockSignal("sync")),
			    presc.enable.eq(interface.enable),
			    prn.shift.eq(presc.output)
			]

		return m

