from amaranth import *
from amaranth.sim import *

# 'naive' 8 bits version of a 1-PPS-synchronized LFSR
class PrnGenerator8bits(Elaboratable):
    def __init__(self):
        # As seen before, the register, its feedback taps
        # and the I/O signals related to it
        self.register = Signal(8,reset = 1)
        self.output = Signal()
        self.input = Signal()
        self.taps = Signal(8, reset = 43) #43 is one of the 8bits m-sequence generator taps 

        # Our 1 pulse per second signal (driven from outside the class)
        self.pps = Signal()

        # A signal that we keep up when we want to generate our PRN
        self.go = Signal()
    
    def elaborate(self, platform):  
        m = Module()

        # If the 1PPS Signal is up, we ((re)start generating our PRN on the next rising edge of our clock
        with m.If(self.pps):
            m.d.sync += [
                # shifting the LFSR
                self.register.eq(self.register.reset),
                self.go.eq(1), #remember to keep generating PRN
            ]
        # keep generating the PRN
        with m.Elif(self.go):
            m.d.sync += [
                self.register.eq(Cat(self.register[1:], self.input)), 
            ]

        m.d.comb += [
            # updating the input and output of the LFSR
            self.input.eq((self.taps & self.register).xor()),
            self.output.eq(self.register[0])
        ]

        return m

if __name__ == "__main__":
    dut = PrnGenerator8bits()
    sim = Simulator(dut)
    
    def proc():
        # emulating a hundred clock cycles
        for i in range(100) :
            # simulating a 1pps impulse at the tenth clock cycle
            if (i == 10 or i == 20 or i == 30) :
                yield dut.pps.eq(1)
            else :
                yield dut.pps.eq(0)
            yield Tick()

    sim.add_clock(1e-6)
    sim.add_process( proc )
    with sim.write_vcd("test.vcd"):
        sim.run()