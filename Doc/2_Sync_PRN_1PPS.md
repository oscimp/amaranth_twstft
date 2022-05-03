# Synchronizing a 1-PPS Signal with our PRN

Previous step : [Generating a PRN](1_PRN.md)

Now that we know how to generate a pseudo-random noise, let's talk about how to use it to transfer our time and frequency information.

TWSTFT transfers frequency and time information through the use of a 1 Pulsation Per Second (1-PPS) signal. The idea behind this is that we have a very precise clock giving us a signal with a rising edge exactly every second. And we want to start modulating our carrier signal with our BPSK modulation at that precise moment. 

Basically, the goal is to restart generating our PRN everytime we receive our 1-PPS signal. Sadly, the LFSR we developped earlier is not that appropriated to enable satellite communication. To improve it, we should :
- Make it generate its PRN at a different rate from the FPGA's clock.
- For comfort reason, we want to make the use of our LFSR as versatile as possible so it should allow the user to change the taps we use while the device is running.
- Make it possible to synchronize its PRN emission everytime we receive a 1-PPS signal, which implies :
    - stop emitting PRN if it's been more than a second since the last PPS Signal,
    - start emitting PRN if we receive a PPS Signal,
    - immediatly interrupt the current sequence to restart it if we receive a PPS Signal.


We will dive into each one of these points in the following sections.

## Slowing down the LFSR with a prescaler

In radiology, it is rare that the default frequency of our FPGA board is exactly the one we want to use for our modulation. So we want to simulate the use of a slower clock... In other words, we need a _Prescaler_. A _Prescaler_ is an electronic block that generates a pulse on its output at a regular interval. 

Maybe you know how to make one IRL, but you can also find an amaranth software version of one [here](../1PPS_Sync/Prescaler.py).

Then we will use this prescaler to cadence our PRN generation as its impulse will be the signal that drives the LFSR shift. 

Which would turn this kind of code :

```python
#shifting operation
m.d.sync += self.reg.eq(Cat(self.reg[1:],insert))
```

into this one :
```python
#same operation but will only be triggered if the prescaler enables it
with m.If(prescaler.output):
    m.d.sync += self.reg.eq(Cat(self.reg[1:],insert))
```

## Making the taps change on the go

Instead of having to always specify the taps to use, it could be useful to change the value of our taps signal by the time the device is running. In order to do it, we can define a memory space in our Module that will be filled by all the taps we may use. 

Such taps values were found by using the algorithms [here](../PRN/msequence.py).

Then, we add a "taps" parameter the PrnGenerator which default value is 0 (as explained in the [previous section](./1_PRN.md), 0 can not be used as taps for our PRN Generation) to know if users want to define the taps themself or if they want to dynamically choose the taps. This will result  in the following construction of the class.

```python
# values of the 32 m-sequence generator taps for 20-bits LFSR
taps20bits = [9, 83, 101, 105, 123, 243, 359, 365, 383, 399,
447, 547, 553, 561, 697, 819, 851, 857, 879, 963,
1013, 1023, 1059, 1157, 1175, 1217, 1223, 1229, 1257, 1289,
1323, 1439]

class PrnGenerator2(Elaboratable):
    def __init__(self, taps = 0):
        # initializing taps when dynamically selected 
		if(taps == 0):
            # as our taps list constains only 32 values,
            # no need to use more than 5 bits to store the address
            # of the selected taps
			self.tsel = Signal(5) 
			
            # this attribute is to remember we choose 
            # taps dynamically among taps20bits 
            # when elaborating
            self._dynamic_tsel = True 

            # here is our memory
			self._mem = Memory(width = 20, # nb of bits used by each value
                                depth=len(taps20bits), # nb of values
                                init = taps20bits # initial value of our memory
            )
            
			self._taps = Signal(20)
		
		# using parameter defined taps
		else:
            # we make sure the taps are not too bad
			assert taps < pow(2,20) 
            assert taps % 2 == 1

            # this attribute is to remember we don't choose taps dynamically 
            # when elaborating
			self._dynamic_tsel = False
			self._taps = Signal(20, reset = taps)
        
        # Finishing the implementation of the constructor ...
    
    def elaborate(self, platform):
        m = Module()

        # remembering to use dynamically chosen taps
		if(self._dynamic_tsel):
			m.d.comb += self._taps.eq(self._mem[self.tsel])
        
        #finishinng the implementation of the elaborate method ...
```

With this implementation, as long as we built our instance of <code>PrnGenerator2</code> with no defined value for <code>taps</code>, we can change the taps we use just by changing the value of <code>self.tsel</code> signal !

## Synchronizing the LFSR with the 1-PPS

### Detecting the 1-PPS signal rise

The 1-PPS signal can occur in 2 different ways :
- The 1-PPS is high shorter than a clock cycle of the FPGA
- The 1-PPS is high longer than a clock cycle of the FPGA


In the first situation, it is possible that we just miss the 1-PPS because it didn't stay in the high state long enough for us to detect it with :
```python
with m.If(pps):
    m.d.sync += [
        # Do something
    ]
```
To avoid this kind of problem, we will choose a clock frequency that is high enough so that it never happens.

however, we can still manage the second situation. The risk here, would be that the <code>pps</code> signal is lasting more than one clock cycle making the previously suggested code execute several times instead of just one. The trick to overcome this problem is to _synchronously_ write down the value of the 1-PPS signal. When doing this, on the next rising edge of the FPGA clock, we can compare the old 1-PPS value with the new one. If they are different and the new one is high, then we just detected a rising edge of the 1-PPS :
```python
m.d.sync += old_pps.eq(self.pps)

with m.If( (old_pps ^ self.pps) & self.pps ):
	m.d.sync += [
		# some code that just has 
        # to be executed on the pps rising edge
	]
```

### Generation of the PRN triggered by the 1-PPS signal



Next step : [Carrier signal generation](3_Clk_Generation.md)