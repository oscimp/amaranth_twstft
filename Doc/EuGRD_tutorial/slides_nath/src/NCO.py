from amaranth import *
from amaranth.sim import *
from math import cos, pi, ceil, log2


class NCO(Elaboratable):

	
	def __init__(self, tick_freq, resol, max_freqout, granularity=1):
		
		
		self.gain_bits =  ceil(log2(tick_freq))
		self.acc_size = ceil(log2(tick_freq/granularity))
		self._accu = Signal(self.acc_size+self.gain_bits)
		self.unit = int(pow(2,ceil(log2(tick_freq*tick_freq//granularity)))/tick_freq)
			
		self.tick = Signal()
		
		self.input = Signal(range(max_freqout))
		
		self.output = Signal(resol)
		self.expected_overflow = pow(2,self.acc_size)*tick_freq
		
		
		discret_cos = []
		pts = int(pow(2,resol))
		self.pts = Signal(resol+1,reset =pts)
		
		for i in range(pts):
			val = cos((i*2*pi)/pts)
			positive = (val+1)/2
			readable = int(positive*(pts-1))
			discret_cos.append(readable)
		
		
		self._cosine = Memory(width = resol, depth=pts, init = discret_cos, name=f"cosine_{pts}pts")
		self._resol = resol
		
		
		self._tick_freq = tick_freq
	
	def elaborate(self, platform):
		m = Module()
		
		step = Signal(self.acc_size+self.gain_bits)
		m.d.comb += [
			step.eq(self.input *self.unit),
			self.output.eq(self._cosine[self._accu[-self._resol:]])
		]
		with m.If(self.tick):
			m.d.sync+= [
				self._accu.eq(self._accu+step),
			]
		
		return m

do = 262
re = 294
mi = 329
fa = 349
sol = 392
la = 440
si = 493
do2 = 2*do
re2 = 2*re
mi2 = 2*mi
		
if __name__ == "__main__":
	tick_freq = int(48e3)
	nb_bits = 8
	max_freqout = 1000
	dut = NCO(tick_freq, nb_bits, max_freqout)
	nb_bits = 9
	sim = Simulator(dut)
	
	def proc():
		f = open("music.bin", "wb")
		data_size = ceil(nb_bits/8)
		noire = tick_freq//2
		croche = tick_freq//4
		print("re")
		yield dut.input.eq(re2)
		yield dut.tick.eq(1)
		
		for _ in range(noire):
			yield Tick()
			val = yield dut.output
			f.write(val.to_bytes(data_size,byteorder='little'))
			
		
		print("mi")
		yield dut.input.eq(mi2)
		for _ in range(croche):
			yield Tick()
			val = yield dut.output
			f.write(val.to_bytes(data_size,byteorder='little'))
			
		print("re")
		yield dut.input.eq(re2)
		for _ in range(croche):
			yield Tick()
			val = yield dut.output
			f.write(val.to_bytes(data_size,byteorder='little'))
		print("do")
		yield dut.input.eq(do2)
		for _ in range(noire):
			yield Tick()
			val = yield dut.output
			f.write(val.to_bytes(data_size,byteorder='little'))
			
		print("la")
		yield dut.input.eq(la)
		for _ in range(noire):
			yield Tick()
			val = yield dut.output
			f.write(val.to_bytes(data_size,byteorder='little'))
		
		print("sol")
		yield dut.input.eq(sol)
		for _ in range(noire):
			yield Tick()
			val = yield dut.output
			f.write(val.to_bytes(data_size,byteorder='little'))
		
		print("la")
		yield dut.input.eq(la)
		for _ in range(croche):
			yield Tick()
			val = yield dut.output
			f.write(val.to_bytes(data_size,byteorder='little'))
		
		print("do")
		yield dut.input.eq(do2)
		for _ in range(croche):
			yield Tick()
			val = yield dut.output
			f.write(val.to_bytes(data_size,byteorder='little'))
		
		print("re")
		yield dut.input.eq(re2)
		for _ in range(noire):
			yield Tick()
			val = yield dut.output
			f.write(val.to_bytes(data_size,byteorder='little'))
		
		print("do")
		yield dut.input.eq(do2)
		for _ in range(croche):
			yield Tick()
			val = yield dut.output
			f.write(val.to_bytes(data_size,byteorder='little'))
		print("done")
		f.close()

	sim.add_clock(1/tick_freq)
	sim.add_process(proc)
	
	with sim.write_vcd("test.vcd"):
		sim.run()
