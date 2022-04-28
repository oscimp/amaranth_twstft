from amaranth import *
from amaranth.sim import *
from Prescaler import *

 # not the experimental values for test reasons (.vcd file would be tooo large)
freqin = 10000
freqout = 2500

class SyncPrnGenerator(Elaboratable):

	def __init__(self): 

		self.reg = Signal(8,reset = 1) #LFSR (using 1 as seed is totally arbitrary)
		self.tick = Signal() # Signal that's driving the LFSR shift
		self.pps = Signal() # Signal on which to (re)start generating a PRN
		self.output = Signal() # Output bit of the LFSR
		self.insert = Signal() # Inpout bit of the LFSR (computed with the LFSR and the taps)

		# remaining amount of clock signal to keep generating PRN before stopping 
		# (we should also reset it every time we receive a pps)
		self.count = Signal(32 ,reset=freqout-1) 
		
		# storing in memory the taps to use so that we can change them dynamically
		self.taps = Signal(8, reset = 43) 
	
	def elaborate(self, platform):
		m = Module()

		# used to generate PRN at 2.5 MHz rate instead of 10 MHz (spectral congestion reasons)
		m.submodules.presc = presc = Prescaler(freqin, freqout) 

		m.d.comb += [
			self.insert.eq((self.taps & self.reg).xor()), # the input bit of the LFSR is calculated this way 
			self.output.eq(self.reg[0]), # the output bit of the register is the lsb of the LFSR
		]

		with m.FSM():
			with m.State("WAIT"):
				with m.If(self.pps):
					m.next = "GENERATE"
				 
			with m.State("GENERATE"):	
				with m.If(presc.output):  # we actualize state of the LFSR on the prescaler's output
					m.d.sync += [
						self.reg.eq(Cat(self.reg[1:],self.insert)),
						self.count.eq(self.count-1)
					]
					with m.If(self.count == 0):
						m.d.sync+=[
							self.count.eq(self.count.reset),
							self.reg.eq(self.reg.reset)
						]
						with m.If(self.pps != 1):
							m.next = "WAIT"
		return m

if __name__ == "__main__" :
	
	dut = SyncPrnGenerator()
	sim = Simulator(dut)
	def proc():
		# Simulating 2 hours of execution (but to test faster, we do as if 1 hour = 3 sec lol)
		# a i-loop cycle is composed of : 
		#		- 3 * freqin clock cycles where nothing is happening //simulating one hour of no signal
		#		- 3 * freqin clock cycles where the PrnGenerator receives a pps every freqin clock cycles
		for i in range(2) :
			count = 0
			print("empty hour " + str(i))
			for _ in range(3 * freqin):
				yield Tick()
			print("pps hour " + str(i))
			for _ in range(3 * freqin):
				if(count%freqin==0):
					yield dut.pps.eq(1)
				else:
					yield dut.pps.eq(0)
				yield Tick()
				count +=1
	
	sim.add_clock(1/freqin)
	sim.add_process(proc)
	with sim.write_vcd("test.vcd"):
		sim.run()