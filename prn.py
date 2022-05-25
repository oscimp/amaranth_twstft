#!/usr/bin/env python3

from amaranth import *
from amaranth.sim import *
from math import log
import pickle
from os.path import exists
from math import ceil


#Here is a small amount of functions that are used to calculate, 
#store and retrieve adequat taps to generate maximum length PRN sequences

pickle_file = "../saved_taps.pickle" #the file used to store the taps

taps_dict = {} #the dict

def unary_xor(x):
	"""if x == 0b0101101, returns 0^1^0^1^1^0^1"""
	res = x & 1
	for i in range(1,int.bit_length(x)):
		x=x>>1
		res ^= 1 & x
	return res

def nextstate(current, code,bit_len):
	"""returns the next state of the LFSR 
	following its size(bit_len), the taps 
	(code) and its current state (current)"""
	bit = unary_xor(current & code)
	res = current >> 1
	res |= bit << (bit_len-1)
	return res

def m_seq_codes(bit_len, limit = 10):
	"""generates (limit) codes which binary values 
	represent where to put the taps on an LFSR to 
	generate a m-sequence of (bit_len) bits values"""
	codes = []
	first = 0x1
	
	codes_to_test = [2*i +1 for i in range(ceil(pow(2,bit_len)/2))]
	print(f"Finding at most {limit} taps for a {bit_len} bits msequence... This may take a while...") 
	for code in codes_to_test:
		test = first
		
		for j in range((pow(2,bit_len)-2)) : 
			test = nextstate(test, code, bit_len)
			
			if (test == first or test == 0):
				break
			
			
		if (test != first and test !=0):
			print(f"{code} is a m-sequence generator taps")
			codes.append(code)
			limit-=1
			if limit == 0 :
				break
	return codes

def write_prn_seq(file, bitlen, code, seed=1, seqlen = 2500000):
	"""creates a file with the PRN sequence associated to the parameters"""
	with open(file,"wb") as f:
		v = seed
		for i in range(seqlen):
			f.write((v%2).to_bytes(1,byteorder='big'))
			v = nextstate(v,code,bitlen)
		f.close()


def taps_autofill(bit_len, nbtaps,save_file=pickle_file):
	"""saves {nbtaps} {bit_len} bits taps inside the parameter defined pickle_file"""
	global taps_dict
	if (bit_len in taps_dict and nbtaps <= len(taps_dict[bit_len])) :
		print(f"{bit_len} bits taps already saved)")
		return
	if exists(save_file) :
		with open(save_file,"rb") as f:
			taps_dict = pickle.load(f)
			f.close()
			if bit_len in taps_dict :
				if nbtaps <= len(taps_dict[bit_len]) :
					print(f"{bit_len} bits taps already saved")
					return

	taps = m_seq_codes(bit_len,nbtaps)
	set_taps(bit_len, taps, save_file = save_file)


def set_taps(bit_len,taps, save_file=pickle_file):
	"""saves the parameter bit_len taps list inside the parameter defined pickle_file
	If the pickle file already contains taps for this bit length, it saves the new taps 
	only if there are more taps inside"""
	global taps_dict
	print("Checking for saved taps...")
	if exists(save_file) :
		with open(save_file,"rb") as f:
			taps_dict = pickle.load(f)
			print("checking for taps existence")
			if bit_len in taps_dict :
				if len(taps) > len(taps_dict[bit_len]):
					print(f"Updating {bit_len} bits taps.")
					taps_dict[bit_len] = taps
				else :
					print(f"Nothing to do, there are saved taps for {bit_len} bits already.")
			else :
				print(f"Adding {bit_len} bits taps to the taps dictionary.")
				taps_dict[bit_len] = taps
			f.close()
	else :
		print(f"No {save_file}, creating one")
		taps_dict[bit_len] = taps
	
	with open(save_file, 'wb') as f:
		pickle.dump(taps_dict,f)
		f.close()

def get_taps(bit_len,save_file=pickle_file):
	"""returns the taps saved in the pickle file for the parameter defined nuber of bits"""
	global taps_dict
	if bit_len in taps_dict :
		return taps_dict[bit_len]
	if exists(save_file) :
		with open(save_file,"rb") as f:
			taps_dict = pickle.load(f)
			f.close()
			if bit_len in taps_dict :
				return taps_dict[bit_len]
	print(f"No taps found for {bit_len} bits ")
	return []


#default number of different taps to choose among when dynamically selecting the taps for the LFSR
nb_taps_auto = 32

class PrnGenerator(Elaboratable):
	"""A synchronizable version of the n-bits PRN Generator to use along the 1-PPS Signal
	
    Parameters
    ----------
    bit_len : greater than 1 integer
    	the number of bits of our LFSR
    
    taps : less than 2^(bit_len)-1 positive integer
		the taps to apply to our LFSR
		if set to zero, we consider the taps as dynamically 
		chosen by the signal `tsel` (see below attributes)
	
	seed : less than 2^(bit_len)-1 non-zero positive integer
		the initial state of the LFSR
		(1 by default)
	
		
    Attributes
    ----------
	output : Signal()
		the output of the LFSR
		
	reg : Signal(bit_len)
		the LFSR used to compute the prn
	
	enable : Signal()
		the enable signal of the PRN Generator 
		keeps the LFSR in its initial state as long as the signal is set to 0
	
	next : Signal()
		shifts the LFSR on every rising clock edge as long as it is set to 1
	
	tsel : Signal(x)
		x corresponds to the number of bits required to 
		count up to the number of taps stored.
		(5 by default as there are at most 32 different taps stored 
		(change it by resetting the value of nb_taps_auto))
		Its value corresponds to the address of the taps stored in memory
		when driven from outside the module, allows to change dynamically 
		the taps used on our LFSR. 
		This can only be used when the `taps` parameter is 0
	
	_dynamic_tsel : Boolean
		true when taps are defined dynamically
	
	_mem : Memory()
		the place where dynamically used taps are stored
		Only exists when the `taps` parameter is 0
	
	_taps : Signal(20)
		signal used as taps for the LFSR
    """
    
	def __init__(self,bit_len, taps = 0,seed = 1):
		#check for a few assertions before working
		assert bit_len > 1
		assert taps >= 0
		assert seed.bit_length() <= bit_len
		
		# initializing taps when dynamically selected 
		if(taps == 0):
			#dynamically getting the taps to use thank to functions defined above
			taps_list = get_taps(bit_len)
			if (len(taps_list)==0) :
				taps_autofill(bit_len, nb_taps_auto)
				taps_list = get_taps(bit_len)
			
			self.tsel = Signal(int(log(nb_taps_auto,2)), name="prn_taps_select")
			self._dynamic_tsel = True
			self._mem = Memory(width = bit_len, depth=len(taps_list), init = taps_list, name="prn_taps_list")
			self._taps = Signal(bit_len, name="prn_used_taps")
		
		# using parameter defined taps
		else:
			#coherent taps should be odd and use at most bit_length bits
			assert taps.bit_length() <= bit_len
			assert taps % 2 == 1 
			self._dynamic_tsel = False
			self._taps = Signal(bit_len, reset = taps, name="prn_used_taps")

		self.next = Signal(name="prn_next")
		self.enable = Signal(reset = 0,name="prn_enable")
		self.reg = Signal(bit_len, reset = seed, name="prn_register")
		self.output = Signal(name="prn_output")
		self.output2 = Signal(name="prn_output2")
	
	def elaborate(self,platform):
		m = Module()

		if(self._dynamic_tsel):
			m.d.comb += self._taps.eq(self._mem[self.tsel])

		insert = Signal(name="register_input")
		m.d.comb += [
			insert.eq((self._taps & self.reg).xor()),
			self.output.eq(self.reg[0]),
			self.output2.eq(self.reg[1]),
		]

		with m.If(self.next):
			with m.If(self.enable):
				m.d.sync += [
					self.reg.eq(Cat(self.reg[1:],insert)),
				]
		with m.If(self.enable==0):
			m.d.sync += [
				self.reg.eq(self.reg.reset)
			]

		return m

if __name__ == "__main__":
	dut = PrnGenerator(8,seed = 0xFF)
	sim = Simulator(dut)
	def proc():
		yield Tick()
		yield dut.enable.eq(1)
		yield dut.next.eq(1)
		for i in range(pow(2,10)):
			if i %300 == 0 :
				yield dut.tsel.eq(dut.tsel+1)
			yield Tick()
	sim.add_clock(1e-6)
	sim.add_process(proc)
	with sim.write_vcd("test.vcd"):
		sim.run()
		
