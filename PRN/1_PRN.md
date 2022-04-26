# Pseudo-Random Noise Generation

It's no surprise that the use electromagnetic waves is required if we want to use satellite communication. however, the nature of the information we share makes it not so easy to transmit. We want to share a frequency information. Which is basically just a signal that's repeated over and over again. But the fact that this information is being repeated AND carried by a periodic signal is complicating the task. It's as if we were to diferenciate a sinusoid to another one with a 2pi phase shift. In such case, how to make the difference between our 1-PPS signal and the same signal a few milliseconds later ?

The solution ? __Binary Phase Shift Keying__ (BPSK) modulation. 

This kind of modulation allows us to transmit binary informations through the phase of our carrier signal. Whenever a 0 turns into a 1 (and vice-versa), the modulation applies a $\pi$ phase shift. 

<img src="../figures/BPSK.png">

We want to use this method to create a 1-PPS signal. So we need to make sure that the information carried does not repeat itself. This way, the auto-correlation of the signal gives us a one when the phase shift is 0 and a close-from-zero value otherwise. Which implies that we are able to differenciate the begining of the signal and subsequently, distinguish our 1_PPS within the received signal.

## Linear Feedback Shift Register

A common way to generate bits at a very high rate is to use a Linear Feedback Shift Register (LFSR). 
It consists in a certain amount of Flip-Flops which contain 1 bit each. Every time the clock signal associated to the register is triggered, each FF gives its value to the following one. The last bit is used as the output of the register and the first bit is retrieved by a linear operation on the different bits of the current state of the LFSR.

<img src="../figures/LFSR.png">

The _linear operation_ in the figure above consists in a bunch of xor doors.

The current binary value stored in the LFSR is called the _state_. The initial tstate is called the _seed_ and the places where we put the xor doors are called _taps_. The bit sequence produced depends on the _seed_ and the _taps_.

As the operation doesn't change along the processing, and as the register has a finite number of different states ($2^n$ for an $n$ bits register), the LFSR has to produce a periodical bit sequence. So if we want to generate a certain PRN, we first need to make sure that the period of the sequence is long enough. 

There are mathematical proofs that well defined taps for an $n$ bits LFSR lead to a sequence of maximum length $2^n-1$ (m-sequences) and we want to use these taps to generate our PRN. To ensure the PRN is long enough, we also choose a resonable bit length for the LFSR. 

So now, let's implement this !

In a first time, we'll just code an 8-bits LFSR with amaranth. 
Then, we'll code a little algorithm to compute taps positions that will generate an m-sequence for a given bit-length.

```python
from amaranth import *

class LFSR_8(Elaboratable):
    def __init__(self, seed,taps, sequence_len):

        # Here is our register
        self.register = Signal(8,reset = seed) 

        # The output of our LFSR
        self.output = Signal()
        # The result of the linear operation 
        # on the bits of the LFSR
        self.input = Signal() 

        # The binary value that represents 
        # which bits to use for our xor operation.
        # A value of 0x0B means the input will be 
        # bit_0 ^ bit_1 ^ bit_3
        self.taps = Signal(8, reset = taps)
        
        #the number of bits to generate for our PRN
        self.count = Signal(8, reset = sequence_len)
    
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
```

A quite different version is given as example [here](./LFSR.py). Though, it computes the exact same sequence. Its script allows us to simulate this program's execution on a FPGA board. 

The parameters used here are :
    seed = 0xFF
    taps = 0x2D
    sequence_len = 20 

<img src="../figures/PRN8.png">

As you can see (and as expected), the sequence generated restarts after the 20th tick of the clock and the state of the register is shifted right. 

Alright ! So now that we have a shift register, let's talk about the taps to use.
