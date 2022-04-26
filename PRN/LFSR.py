from amaranth import *
from amaranth.sim import *
from math import pow


class LFSR_n(Elaboratable):
    def __init__(self, size, seed,taps, sequence_len):
        assert size >= taps.bit_length()
        assert size >= seed.bit_length()
        assert pow(2,size)-1 >= sequence_len
        assert seed != 0

        # Here is our register
        self.register = Signal(size,reset = seed) 

        # The output of our LFSR
        self.output = Signal()
        # The result of the linear operation 
        # on the bits of the LFSR
        self.input = Signal() 

        # The binary value that represents 
        # which bits to use for our xor operation.
        # A value of 0x0B means the input will be 
        # bit_0 ^ bit_1 ^ bit_3
        self.taps = Signal(size, reset = taps)
        
        #the number of bits to generate for our PRN
        self.count = Signal(size, reset = sequence_len)
    
    def elaborate(self, platform):  
        m = Module()

        # Whenever the clock signal of the PRN generator is at high,
        # we update the register
        m.d.sync += [
            #appending the input to our shifted register
            self.register.eq(Cat(self.register[1:], self.input)), 
            #counting down the number of bits to generate
            self.count.eq(self.count - 1)
        ]

        # When the sequence is long enough, we restart
        with m.If(self.count==0):
            m.d.sync += [
                self.count.eq(self.count.reset),
                self.register.eq(self.register.reset)
            ]
        
        m.d.comb += [
            # Accomplishing the linear combination of the bits defined by the taps
            self.input.eq((self.taps & self.register).xor()),
            # updating the output of the LFSR
            self.output.eq(self.register[0])
        ]

        return m

if __name__ == "__main__" :
    size = 8
    taps = 0x2D
    seed = 0xFF
    sequence_len = 20

    prn_gen = LFSR_n(size,seed,taps,sequence_len)

    sim = Simulator(prn_gen)

    def proc():
        for i in range(3*sequence_len):
            yield Tick()
    
    sim.add_clock(1e-6)
    sim.add_process(proc)
    with sim.write_vcd("test.vcd"):
        sim.run()
