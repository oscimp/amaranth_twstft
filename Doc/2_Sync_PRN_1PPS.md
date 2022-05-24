# Synchronizing a 1-PPS Signal with our PRN

Previous step : [Generating a PRN](1_PRN.md)

Now that we know how to generate a pseudo-random noise, let's talk about how to use it to transfer our time and frequency information!

TWSTFT transfers frequency and time information through the use of a 1 Pulsation Per Second (1-PPS) signal accompanied by a 2.5MHz clock. The idea behind this is that we have a very precise clock giving us a signal with a rising edge exactly every second. And we want to start modulating our carrier signal with our BPSK modulation at that precise moment. The frequency that defines the modulation is the 2.5 MHz signal, also given by the so-said very precise clock.

Basically, the goal is to restart generating our PRN everytime we receive our 1-PPS signal. But sadly, the LFSR we developped earlier is not that appropriated to enable satellite communication because of a few details. To improve it, here are a some things we can do :
- Making it generate its PRN at a different rate from the FPGA's clock (in fact, it should be based on the 2.5 MHz signal),
- For comfort reason, we want to make the use of our LFSR as versatile as possible so it should allow the user to change the taps we use while the device is running.
- Making it possible to synchronize its PRN emission everytime we receive a 1-PPS signal, which implies :
    - stop emitting PRN when the LFSR has produce an arbitrary number of bits (for example, 2.5e6 bits, because it should be the number of bits we generate during a second when our PRN rate is 2.5MHz),
    - start emitting PRN if we receive a PPS Signal,
    - immediatly interrupt the current sequence to restart it if we receive a PPS Signal.


We will dive into each one of these points in the following sections.

## Slowing down the LFSR with a prescaler

In radiology, it is rare that the default frequency of our FPGA board is exactly the one we want to use for our modulation. In our case, we are working with a 630MHz clock. So we want to simulate the use of a slower clock... In other words, we need a _Prescaler_. A _Prescaler_ is an electronic block that generates a pulse on its output at regular interval. if we want to go from 630MHz to 2.5 MHz, we need to produce a tick every 252 clock rising edge (252*2.5=630).

Maybe you know how to make a prescaler IRL, but you can also find an amaranth software version of one [here](../1PPS_Sync/Prescaler.py). This one also allows to enable/disable the emission of the output signal through the use of an input signal that should be driven from outside the module.

Then we will use this prescaler to cadence our PRN generation as its impulse will be the signal that drives the LFSR shift. Let's say our FPGA board's frequency is `freqin`, if we want to execute an operation with a frequency `freqout`, we would turn this kind of code :

```python
#shifting operation
m.d.sync += self.reg.eq(Cat(self.reg[1:],insert))
```

into this one :
```python
#Instanciating our prescaler
presc = Prescaler(freqin, freqout)

#authorizing the prescaler to emit
m.d.comb += presc.enable.eq(1)

#Same operation as before but it will only be triggered only if the prescaler enables it
with m.If(presc.output):
    m.d.sync += self.reg.eq(Cat(self.reg[1:],insert))
```

## Making the taps change on the go

Instead of having to always specify the taps to use, it could be useful to change the value of our taps signal by the time the device is running. In order to do it, we can define a memory space in our Module that will be filled by all the taps we may use. 

Such taps values were found by using the algorithms [here](../PRN/msequence.py).

Then, we add a "taps" parameter to the PrnGenerator which default value is 0 (as explained in the [previous section](./1_PRN.md), 0 can not be used as taps for our PRN Generation) to know if users want to define the taps themself or if they want to dynamically choose the taps. This will result  in the following construction of the class.

```python
# values of the 32 m-sequence generator taps for a 20-bits LFSR
taps20bits = [9, 83, 101, 105, 123, 243, 359, 365, 383, 399,
447, 547, 553, 561, 697, 819, 851, 857, 879, 963,
1013, 1023, 1059, 1157, 1175, 1217, 1223, 1229, 1257, 1289,
1323, 1439]

class PrnGenerator20(Elaboratable):
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
			
			self._taps = Signal(20) # 20 bits like the LFSR length
		
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

With this implementation, as long as we build our instance of <code>PrnGenerator20</code> with no defined value for <code>taps</code>, we can change the taps we use just by changing the value of <code>self.tsel</code> signal !

## Synchronizing the LFSR with the 1-PPS signal

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
To avoid this kind of problem, we will choose a clock frequency that is high enough so that it never happens (ie : 630MHz in our case).

However, we can still manage the second situation. The risk here, would be that the `pps` signal is lasting more than one clock cycle making the previously suggested code execute several times instead of just one. The trick to overcome this problem is to _synchronously_ write down the value of the 1-PPS signal. When doing this, on the next rising edge of the FPGA clock, we can compare the old 1-PPS value with the new one. If they are different and the new one is high, then we just detected a rising edge of the 1-PPS :
```python
m.d.sync += old_pps.eq(self.pps)

with m.If( (old_pps ^ self.pps) & self.pps ):
	m.d.sync += [
		# some code that just has 
        # to be executed on the pps rising edge
	]
```

### Generation of the PRN triggered by the 1-PPS signal

To keep our code as modular as possible, we will prefer to develop separatly the implementation of our PRN generator and the synchronization of it with the 1-PPS.

As we need to get the LFSR to stop and go on demand, we can add to it an `enable` signal that will keep the LFSR in its initial state for as long as `enable` is low. When it goes high, the LFSR starts generating the PRN.

So in the end, the elaborate method of our PrnGenerator looks like this :

```python
	def elaborate(self,platform):
		m = Module()

		if(self._dynamic_tsel): #coping with the fact we could use dinamically defined taps
			m.d.comb += self._taps.eq(self._mem[self.tsel])

		insert = Signal()
		
		m.d.comb += [
			insert.eq((self._taps & self.reg).xor()),
			self.output.eq(self.reg[0]),
		]

		with m.If(self.next): # when we receive the signal that we can shift (typically, self.next==output of the prescaler)
			with m.If(self.enable): # allowing with an enable signal to reset or keep going the LFSR
				m.d.sync += [
					self.reg.eq(Cat(self.reg[1:],insert)),
				]
			with m.Else():
				m.d.sync += [
					self.reg.eq(self.reg.reset)
				]

		return m
```

In this portion of code, we remark that there are 3 signals used in our LFSR that are not directly driven within the implementation of it. This means we will have to set ourself the values of `self.enable` and  `self.next` (and perhaps `self.tsel`) from _outside_ the class. Which is fine because we need to use our own prescaler as a `next` signal, and our 1-PPS rising edge as the deassertion condition for the `enable` signal.

### Making the PPS, Prescaler and LFSR cohabit

As we now have the Prescaler and the LFSR in two different classes, we may want to create a third module to merge them into a uniq module that is receiving a PPS and generating the PRN according to it. So it would only have one input signal (1-PPS) (or two inputs if the taps are dynamically chosen) and one output signal. I should also be parametrized with :
+ the parameters of the LFSR,
+ the number of bits we want to generate each time we receive a pps,
+ the frequency of the clock we use and the frequency of the PRN generation we want. 


So in the end, it should just be a software version of this component :

<img src="../figures/Synchronizer.png">

Such module could be defined in yet another class :

```python
class Synchronizer(Elaboratable):
	"""A module that generates a 20-bits PRN 
    synchronized with a 1-PPS Signal in input
    """
    
    def __init__(self, freqin, freqout, noise_len = pow(2,20)-1, taps=0, seed = 0xFFFFF):
		self.pps = Signal() #PPS input
		self.output = Signal()
		
		#just as for the PRN, we define taps either dynamically or statically
		if taps == 0:
			self.dynamic_taps = True
			self.tsel = Signal(5)
		else :
			self.dynamic_taps = False
			self.taps = taps
			
		#here is the part where we save the arguments for our prescaler and LFSR submodules
		self.seed = seed 
		self._freqin = freqin
		self._freqout = freqout
		self.noise_len = noise_len
	
	def elaborate(self, platform):
		m = Module()

		cnt = Signal(32) #to keep track of how many bits were generated since the last pps
		
		#synchronously saving the value of the pps to detect the rising edge
		old_pps = Signal(name="sync_last_clk_pps") 
		m.d.sync += old_pps.eq(self.pps)
		
		#defining submodules
		if self.dynamic_taps :
			m.submodules.prn = prn = PrnGenerator(seed = self.seed)
			m.d.comb += prn.tsel.eq(self.tsel)
		else :
			m.submodules.prn = prn = PrnGenerator(taps=self.taps, seed=self.seed)
		
		m.submodules.presc = presc = Prescaler(self._freqin, self._freqout)

		#linking the modules between them
		m.d.comb += [
			prn.next.eq(presc.output),
			self.output.eq(prn.output)
		]
		
		#defining the rising edge of the pps signal
		rise = Signal()
		m.d.comb += rise.eq((old_pps ^ self.pps) & self.pps) 
		
		with m.If(cnt<self.noise_len) : #as long as we haven't emitted enough bits
			with m.If(presc.output): #we keep counting them
				m.d.sync += cnt.eq(cnt+1)
			m.d.comb += [ #and we authorize their emission
				presc.enable.eq(1),
				prn.enable.eq(1)
			]
		with m.Else(): #otherwise, we reset the values of the prn and prescaler
			m.d.comb += [
				presc.enable.eq(0),
				prn.enable.eq(0)
			]

		with m.If(rise): #when we receive a pps, we restart counting
			m.d.sync += cnt.eq(0)
		return m
```

And here we are ! By now, our synchronization should be operational.

Next step : [Carrier signal generation](3_Clk_Generation.md)
