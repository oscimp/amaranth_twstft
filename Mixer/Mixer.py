#!/usr/bin/env python3

from amaranth import *
from amaranth.build import *
from amaranth_boards.resources import *
from Synchronizer import *
from Prescaler import *


#Carrier Signal is the "sync clock signal" in our case as the 
#FPGA is going to be triggered by the Atomic Clock Signal

#frequencies used for the prn generation
freqin  = 20000000
freqout =  2500000


#Mixing the carrier signal and a PRN

#carrier signal is our clock
#1PPS Signal is represented by a button trigger

class Mixer(Elaboratable):

	def __init__(self, taps = 0, seed = 0xFFFFF, noise_len = 0):
		self.carrier = Signal()
		self.modulated = Signal()
		self.seed = seed
		self.noise_len = noise_len
		
		if taps==0:
			self.dynamic_taps = True
			self.tsel = Signal(5, reset=0)
		else:
			self.dynamic_taps = False
			self.taps = taps
		
	def elaborate(self,platform):
		m = Module()
		
		#setting clock speed with the PLL
		m.domains.sync = ClockDomain(reset_less=True)
	
		clk_in = platform.request(platform.default_clk)
		platform_freq = platform.default_clk_frequency #20 MHz
		mainpll_feedback = Signal()
		sys_locked	   = Signal()  
		clk70Ph0		 = Signal()  
		clk70Ph90		= Signal()

		platform_period = int(1e9//platform_freq)
		vco_mult = 14
		sync_clk_div = 20
		carrier_clk_div = 18
		
		clk_in_bufg = Signal()
		clk_fast_bufg = Signal()
		
		m.submodules.bufg_in = Instance("BUFG",
			i_I = clk_in,
			o_O = clk_in_bufg
		)
												
		m.submodules.mainpll = Instance("PLLE2_ADV",
			p_CLKIN1_PERIOD		= platform_period, # ns -> 20 MHz	
			p_BANDWIDTH			= "OPTIMIZED",
			p_COMPENSATION		= "ZHOLD",  
			p_STARTUP_WAIT		= "FALSE",
							   
			p_DIVCLK_DIVIDE		= 1,				   
			p_CLKFBOUT_MULT		= vco_mult, # VCO -> 1260MHz
			p_CLKFBOUT_PHASE	= 0.000,
						   
			# clk0: 630MHz			 
			p_CLKOUT0_DIVIDE	= sync_clk_div,	
			p_CLKOUT0_PHASE		= 0.000,
			p_CLKOUT0_DUTY_CYCLE	= 0.500,
			# clk1: 70MHz phase: 0	  
			p_CLKOUT1_DIVIDE	= carrier_clk_div,   
			p_CLKOUT1_PHASE		= 0.000,
			p_CLKOUT1_DUTY_CYCLE	= 0.500,
			# clk2: 70MHz phase: 90	 
			p_CLKOUT2_DIVIDE	= carrier_clk_div,	
			p_CLKOUT2_PHASE		= 90.000,
			p_CLKOUT2_DUTY_CYCLE	= 0.500,
											  
			i_CLKFBIN			= mainpll_feedback,
			o_CLKFBOUT			= mainpll_feedback,
			i_CLKIN1			= clk_in_bufg,			 
			o_CLKOUT0			= clk_fast_bufg,
			o_CLKOUT1			= clk70Ph0,		   
			o_CLKOUT2			= clk70Ph90, 
			o_LOCKED			= sys_locked,
		)
	
		m.submodules.sync_clk_bufg = Instance("BUFG",
			i_I = clk_fast_bufg,
			o_O = ClockSignal("sync"),
		)
		
		clock_freq = int(platform_freq * vco_mult / sync_clk_div)
		
		#parametrizing the platforms outputs
		if platform is not None:
			if (type(platform).__name__ == "ZC706Platform"):
				conn = ("pmod", 0)
				platform.add_resources([
					Resource('pins', 0,
						Subsignal('initial', Pins('4', conn = conn, dir='o')),
						Subsignal('modulated', Pins('1', conn = conn, dir='o')),
						Subsignal('prn', Pins('3', conn = conn, dir='o')),
						Attrs(IOSTANDARD="LVCMOS15")
					)
				])
			
			elif (type(platform).__name__ == "ZedBoardPlatform"):
				connd = ("pmodd",0)
				connb = ("pmodb",0)
				connc = ("pmodc",0)
				
				platform.add_resources([
					Resource('pins', 0,
						
						Subsignal('initial', Pins('4', conn = connb, dir='o')),
						Subsignal('prn', Pins('4', conn = connc, dir='o')),
						Subsignal('test1', Pins('1', conn = connc, dir='o')),
						Subsignal('test2', Pins('2', conn = connc, dir='o')),
						Subsignal('modulated', Pins('4', conn = connd, dir='o')),
						Attrs(IOSTANDARD="LVCMOS33")
					)
				])
			
			pins = platform.request('pins',0)
			
			#setting noise duration
			if self.noise_len > 0:
				noise_len = self.noise_len
			else :
				noise_len = pow(2,20)-1
			
			#setting dynamic usage of taps
			if self.dynamic_taps :
				m.submodules.prn_gen = prn_gen = Synchronizer(clock_freq, freqout, noise_len=noise_len, seed = self.seed )
				m.d.comb += prn_gen.tsel.eq(self.tsel)
			else :
				m.submodules.prn_gen = prn_gen = Synchronizer(clock_freq, freqout, noise_len=noise_len, taps =self.taps, seed = self.seed )
			
			m.d.comb+=[
				self.carrier.eq(ClockSignal("sync")),
				self.modulated.eq(self.carrier ^ prn_gen.output),
			]
			
			if 1 == 1:
				m.submodules.pps_pulse = pps_pulse = Prescaler(clock_freq, 1)
				#new_clk = Signal()
				#with m.If(pps_pulse.output):
				#	m.d.sync += new_clk.eq(~new_clk)
				
				m.d.comb += [
					prn_gen.pps.eq(pps_pulse.output),#new_clk),
					pps_pulse.enable.eq(1),
					pins.test2.eq(pps_pulse.output)
				]
			else:
				pps_cpt = Signal(32)
				pps_pulse = Signal()
				m.d.comb += [
					pps_pulse.eq(0),
					prn_gen.pps.eq(0),
				]
				m.d.sync += pps_cpt.eq(pps_cpt + 1)
				with m.If(pps_cpt == int(clock_freq-1)):
					m.d.sync += pps_cpt.eq(0)
				with m.If(pps_cpt < int(clock_freq //2)):
					m.d.comb += prn_gen.pps.eq(1)
					m.d.comb += pps_pulse.eq(1)
				
				m.d.comb += pins.test2.eq(pps_pulse)
				
			m.d.comb += pins.modulated.eq(self.modulated)
			m.d.comb += pins.prn.eq(prn_gen.output)
			m.d.comb += pins.initial.eq(self.carrier)
			m.d.comb += pins.test1.eq(prn_gen.pps)
			

		return m

