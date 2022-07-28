from amaranth import *
from Prescaler import *
from NCO import *
from amaranth.build import *
from math import log2

sample_rate = int(48e3)
resol = 8
base_band_width = 17000 
radio_carrier = int(70e6) 
excursion = 10

freqin_sim = int(250e6)
nb_bytes_data_sim_write = 1

silence = 0
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
fa2 = 2*fa
sol2 = 2*sol
la2 = 2*la
si2 = 2*la

def get_partition(*args):
	partition = []
	is_a_key = True
	note = 0
	duration = 1
	for arg in args:
		if is_a_key :
			note = arg
		else :
			duration = arg
			for _ in range(duration):
				partition.append(note)
		is_a_key = not is_a_key
	return partition

def define_beat(freqin,beat_duration):
	return Prescaler(freqin, int(1/beat_duration))

class MyRadioEmitter(Elaboratable):
	
	def __init__(self):
		self.input = Signal(range(base_band_width))
		self.output = Signal()
	
	def elaborate(self, platform):
		m = Module()
		
		if platform == None :
			frequency = freqin_sim
		else :
			m.domains.sync = ClockDomain(reset_less=True)
			platform_clk = platform.request(platform.default_clk)
			base_clk_freq    = platform.default_clk_frequency
			mmcm_clk_out     = Signal()
			mmcm_locked      = Signal()
			mmcm_feedback    = Signal()
		
			clk_input_buf    = Signal()
			m.submodules += Instance("BUFG",
				i_I  = platform_clk,
				o_O  = clk_input_buf,
			)
			
			nco_mult = 10.0
			mmc_out_div = 4.0
			mmc_out_period = 1e9 / (base_clk_freq * nco_mult / mmc_out_div)
			
			m.submodules.mmcm = Instance("MMCME2_BASE",
				p_BANDWIDTH          = "OPTIMIZED",
				p_CLKFBOUT_MULT_F    = nco_mult, 
				p_CLKFBOUT_PHASE     = 0.0,
				p_CLKIN1_PERIOD      = int(1e9 // base_clk_freq), # 20MHz
				p_CLKOUT0_DIVIDE_F   = mmc_out_div,
				p_CLKOUT0_DUTY_CYCLE = 0.5,
				p_CLKOUT0_PHASE      = 0.0,
				i_PWRDWN               = 0,
				i_RST                  = 0,
				i_CLKFBIN              = mmcm_feedback,
				o_CLKFBOUT             = mmcm_feedback,
				i_CLKIN1               = clk_input_buf,
				o_CLKOUT0              = mmcm_clk_out,
				o_LOCKED               = mmcm_locked,
			)
		
			m.submodules += Instance("BUFG",
				i_I  = mmcm_clk_out,
				o_O  = ClockSignal("sync"),
			)
			frequency = int(1e9/mmc_out_period)
	
			connd = ("pmodd",0)
			connb = ("pmodb",0)
			connc = ("pmodc",0)
				
			platform.add_resources([
				Resource('pins', 0,
					Subsignal('B1_o', Pins('1', conn = connb, dir='o')),
					Subsignal('B2_o', Pins('2', conn = connb, dir='o')),
					Subsignal('B3_o', Pins('3', conn = connb, dir='o')),
					Subsignal('B4_o', Pins('4', conn = connb, dir='o')),
		
					Subsignal('C1_o', Pins('1', conn = connc, dir='o')),
					Subsignal('C4_i', Pins('4', conn = connc, dir='i')),
		
					Subsignal('D4_o', Pins('4', conn = connd, dir='o')),
					Subsignal('D1_o', Pins('1', conn = connd, dir='o')),
					Attrs(IOSTANDARD="LVCMOS33")
				)
			])
			
			pins = platform.request('pins',0)
	
		m.submodules.sampler = sampler = Prescaler(frequency, sample_rate)
		
		m.submodules.base_band_signal = base_band_signal = NCO(
																sample_rate,
																resol,
																base_band_width
															)
		
		m.submodules.radio_band_signal = radio_band_signal = NCO(
																frequency, 
																1,
																base_band_width*excursion+radio_carrier
															)
		
		m.d.comb += [
			sampler.enable.eq(1),
			radio_band_signal.tick.eq(1),
			base_band_signal.tick.eq(sampler.output),
			base_band_signal.input.eq(self.input),
			radio_band_signal.input.eq(radio_carrier + base_band_signal.output * excursion),
			self.output.eq(radio_band_signal.output)
		]
		
		if platform != None:
			m.submodules.tempo = tempo = define_beat(frequency,0.25)
			
			#TETRIS Partition! (Written with love by Nathan Gallone)
			partition = get_partition(
							mi2,2,
							si,1,
							do2,1,
							re2,2,
							do2,1,
							si,1,
							
							la,2,
							la,1,
							do2,1,
							mi2,2,
							re2,1,
							do2,1,
							
							si,3,
							do2,1,
							re2,2,
							mi2,2,
							
							do2,2,
							la,2,
							la,4,
							
							silence,1,
							re2,2,
							fa2,1,
							la2,2,
							sol2,1,
							fa2,1,
							
							mi2,2,
							silence,1,
							do2,1,
							mi2,2,
							re2,1,
							do2,1,
							
							si,3,
							do2,1,
							re2,2,
							mi2,2,
							
							do2,2,
							la,2,
							la,4
							)
			
			
			time = Signal(range(len(partition)))
			mem = Memory(width = 1+int(log2(max(partition))), depth=len(partition), init = partition, name="partition")
			
			
			with m.If(tempo.output):
				m.d.sync += time.eq(time+1)
			
			m.d.comb+= [
				tempo.enable.eq(1),
				self.input.eq(mem[time]),
				pins.D4_o.eq(self.output)
			]
			
		return m
	
if __name__ == "__main__":
	dut = MyRadioEmitter()
	sim = Simulator(dut)
	
	def proc():
		f = open("music_radio.bin", "wb")
		print("re")
		yield dut.input.eq(re2)
		for _ in range(freqin_sim//200):
			yield Tick()
			val = yield dut.output
			f.write(val.to_bytes(nb_bytes_data_sim_write,byteorder='little'))
			
		
		print("mi")
		yield dut.input.eq(mi2)
		for _ in range(freqin_sim//400):
			yield Tick()
			val = yield dut.output
			f.write(val.to_bytes(nb_bytes_data_sim_write,byteorder='little'))

		f.close()

	sim.add_clock(1/freqin_sim)
	sim.add_process(proc)
	
	with sim.write_vcd("test.vcd"):
		sim.run()
