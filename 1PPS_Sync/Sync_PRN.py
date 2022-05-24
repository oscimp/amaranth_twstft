from amaranth import *
from amaranth.sim import *

# values of the 32 m-sequence generator taps for 20-bits LFSR
taps20bits = [9, 83, 101, 105, 123, 243, 359, 365, 383, 399,
447, 547, 553, 561, 697, 819, 851, 857, 879, 963,
1013, 1023, 1059, 1157, 1175, 1217, 1223, 1229, 1257, 1289,
1323, 1439]


class PrnGenerator(Elaboratable):
	"""A synchronizable version of the 20-bits PRN Generator to use along the 1-PPS Signal

    Parameters
    ----------
    taps : less than 2²⁰-1 positive integer
		the taps to apply to our LFSR
		if set to zero, we consider the taps as dinamically 
		chosen by the signal `tsel` (see below attributes)
	
	seed : less than 2²⁰-1 non-zero positive integer
		the initial state of the LFSR
		(1 by default)
	
	cnt : less than 2²⁰-1 non-zero positive integer
		number of shift iterations of our LFSR before restarting it
		( 2²⁰-1  by default)

    Attributes
    ----------
	output : Signal()
		the output of the LFSR

	reg : Signal(20)
		the LFSR used to compute the prn
	
	reset : Signal()
		the reset signal of the PRN Generator 
		keeps the LFSR in its initial state as long as the signal is set to 1
	
	enable : Signal()
		enable signal of the PRN Generator
		shifts the LFSR on every rising clock edge as long as it is set to 1
	
	tsel : Signal(5)
		its value corresponds to the address of the taps stored in memory
		when driven from outside the module, allows to change dynamically 
		the taps used on our LFSR
		This can only be used when the `taps` parameter is 0
	
	_dynamic_tsel : Boolean
		true when taps are defined dinamically
	
	_mem : Memory()
		the place where dynamically used taps are stored
		Only exists when the `taps` parameter is 0
	
	_taps : Signal(20)
		signal used as taps for the LFSR
	
	_cnt : Signal(20)
		counts the number of remaining states of the LFSR before the next automatic reset
    """
	def __init__(self, taps = 0,seed = 1, cnt = pow(2, 20)-1):
		
		# initializing taps when dynamically selected 
		if(taps == 0):
			self.tsel = Signal(5, name="prn_taps_select")
			self._dynamic_tsel = True
			self._mem = Memory(width = 20, depth=len(taps20bits), init = taps20bits, name="prn_potential_taps")
			self._taps = Signal(20, name="prn_used_taps")
		
		# using parameter defined taps
		else:
			assert taps < pow(2,20)
			assert taps % 2 == 1
			self._dynamic_tsel = False
			self._taps = Signal(20, reset = taps, name="prn_used_taps")

		self.enable = Signal(name="prn_enable")
		self.reset = Signal(name="prn_reset")
		self.reg = Signal(20, reset = seed,name="prn_register")
		self.output = Signal(name="prn_output")
		self._cnt = Signal(20, reset = cnt,name="prn_state_counter")
	
	def elaborate(self,platform):
		m = Module()

		if(self._dynamic_tsel):
			m.d.comb += self._taps.eq(self._mem[self.tsel])

		insert = Signal(name="register_input")
		m.d.comb += [
			insert.eq((self._taps & self.reg).xor()),
			self.output.eq(self.reg[0]),
		]

		with m.If(self.reset):
			m.d.sync += [
				self._cnt.eq(self._cnt.reset),
				self.reg.eq(self.reg.reset)
			]
		with m.Else():
			with m.If(self.enable):
				m.d.sync += [
					self.reg.eq(Cat(self.reg[1:],insert)),
					self._cnt.eq(self._cnt-1)
				]
				with m.If(self._cnt == 0):
					m.d.sync += [
						self._cnt.eq(self._cnt.reset),
						self.reg.eq(self.reg.reset)
					]


		return m

#run "python3 {thisfile}" to start this simulation
#You can use GTKWave to visualize the result of the simulation below 
#and check if the architecture defined above is correct
#(it doesn't mean you won't have any trouble whe flashing on your FPGA as each board may have its own limits)
if __name__ == "__main__":
	if False : #test with user defined taps
		dut = PrnGenerator(taps = 83, seed = 0xFFFFF, cnt = 1024)
		sim = Simulator(dut)

		def proc():
			for i in range(42) :
				yield Tick()
			for i in range(1515):
				if (i%2 == 0):
					yield dut.enable.eq(1)
				else :
					yield dut.enable.eq(0)
				yield Tick()
	
		sim.add_clock(1e-6)
		sim.add_process(proc)
		with sim.write_vcd("test.vcd"):
			sim.run()
	else : #test with dynamically defined taps
		dut = PrnGenerator(seed = 0xFFFFF, cnt = 1024)
		sim = Simulator(dut)
		
		def proc():
			tap_no = 0
			yield dut.tsel.eq(tap_no)
			for i in range(42) :
				yield Tick()
			for i in range(1515):
				if(i%100 == 0):
					tap_no +=1
					yield dut.tsel.eq(tap_no)
				if (i%2 == 0):
					yield dut.enable.eq(1)
				else :
					yield dut.enable.eq(0)
				yield Tick()
	
		sim.add_clock(1e-6)
		sim.add_process(proc)
		with sim.write_vcd("test.vcd"):
			sim.run()
