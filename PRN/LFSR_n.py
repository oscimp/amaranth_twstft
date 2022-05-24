from amaranth import *
from amaranth.sim import *
from math import pow


class LFSR_n(Elaboratable):
    """an Amaranth generic implementation of a Linear Feedback Shift Register

    Parameters
    ----------
    size : non-zero positive int 
        the bit length of the LFSR
        
    seed : non-zero positive int smaller than 2^size
        the value that initializes our LFSR

    taps : positive int smaller than 2^size
        The binary value that represents 
        which bits to use for our xor operation.
        A value of 0x0B means the input of our register will be 
        bit_0 ^ bit_1 ^ bit_3

    sequence_len : positive integer smaller than 2^size - 1
        the number of bits to generate with our lfsr.

    Attributes
    ----------
    register : Signal(size)
    output : Signal()
    _taps : Signal(size)
    _count : Signal(size)

    """

    def __init__(self, size, seed, taps, sequence_len):
        assert size >= taps.bit_length()
        assert size >= seed.bit_length()
        assert pow(2,size)-1 >= sequence_len
        assert seed != 0

        self.register = Signal(size,reset = seed) 

        self.output = Signal()

        self._taps = Signal(size, reset = taps)
        
        #the number of bits to generate for our PRN
        self._count = Signal(size, reset = sequence_len)
    
    def elaborate(self, platform):  
        m = Module()

        # The result of the linear operation 
        # on the bits of the LFSR
        insert = Signal() 
        
        # Whenever the clock signal of the PRN generator is at high,
        # we update the register
        m.d.sync += [
            #appending the insert to our shifted register
            self.register.eq(Cat(self.register[1:], self.insert)), 
            #counting down the number of bits to generate
            self._count.eq(self._count - 1)
        ]

        # When the sequence is long enough, we restart
        with m.If(self._count==0):
            m.d.sync += [
                self._count.eq(self._count.reset),
                self.register.eq(self.register.reset)
            ]
        
        m.d.comb += [
            # Accomplishing the linear combination of the bits defined by the taps
            self.insert.eq((self._taps & self.register).xor()),
            # updating the output of the LFSR
            self.output.eq(self.register[0])
        ]

        return m

#run "python3 {thisfile}" to start this simulation
#You can use GTKWave to visualize the result of the simulation below 
#and check if the architecture defined above is correct
#(it doesn't mean you won't have any trouble whe flashing on your FPGA as each board may have its own limits)
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
