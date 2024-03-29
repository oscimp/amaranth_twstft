# Synchronizing a 1-PPS Signal with our PRN
Back to the [README](../README.md)
Previous step : [Generating a PRN](02_PRN.md)

Now that we know how to generate a pseudo-random noise, let's talk about how to use it to transfer our time and frequency information!

TWSTFT transfers frequency and time information through the use of a 1 Pulse Per Second (1-PPS) signal accompanied by a 10MHz reference clock. A reference clock signal is used to clock the FPGA while the rising edge of the PPS defines every second. We must start modulating the carrier signal with a phase modulation at the rising edge of the PPS and run the pseudo random sequence from there. The PRN bitrate is 2.5 MHz or one fourth of the reference clock to meet the analog bandwidth of the allocated radiofrequency link.

The objective of the gateware is to start generating our PRN everytime we receive our 1-PPS signal. But sadly, the LFSR we developped earlier is not that appropriated to enable satellite communication because of a few details. To improve it, here are a some things we can do:
- Making it generate its PRN at a different rate from the FPGA clock (in fact, it should be based on the 2.5 MHz signal),
- For comfort reason, we want to make the use of our LFSR as versatile as possible so it should allow the user to change the taps we use while the device is running.
- Making it possible to synchronize its PRN emission everytime we receive a 1-PPS signal, which implies :
    - stop emitting PRN when the LFSR has produce an arbitrary number of bits (for example, 2.5e6 bits, because it should be the number of bits we generate during a second when our PRN rate is 2.5MHz),
    - start emitting PRN if we receive a PPS Signal,
    - immediatly interrupt the current sequence to restart it if we receive a PPS Signal.

We will dive into each one of these points in the following sections.

## Slowing down the LFSR with a prescaler

Selecting the radiofrequency carrier freaquency as the rate clocking the FPGA board would be inefficient and restrictive. In our case, we are working with a 630MHz clock. So we want to simulate the use of a slower clock... In other words, we need a _prescaler_. A _prescaler_ is an electronic block that generates a pulse on its output at regular interval. if we want to go from 630MHz to 2.5 MHz, we need to produce a tick every 252 clock rising edge (252x2.5=630).

An implementation of a prescaler in the amaranth language is provided [here](../Prescaler.py). This program also allows to enable/disable the emission of the output signal through the use of an input signal that should be driven from outside the module.

We will use this prescaler to clock the PRN generator as its impulse will be the signal that drives the LFSR shift register. Considering that the FPGA board input frequency is `freqin`, if we want to execute an operation with a frequency `freqout`, we would turn this kind of code:

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

Instead of having to always specify the taps to use, it could be useful to change the value of the taps by the time the device is running. In order to do it, we can define a memory space in the Module that will be filled by all the taps we may use. 

Such tap values were found by using the algorithms of the [prn.py](../prn.py) file.

Then, we add a "taps" parameter to the PrnGenerator whose default value is 0 (as explained in the [previous section](./1_PRN.md), 0 can not be used as taps for our PRN Generation) to know if users want to define the taps themselves or if they want to dynamically choose the taps. This will result  in the following construction of the class.

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

With this implementation, as long as the instance of <code>PrnGenerator20</code> is built with no defined value for <code>taps</code>, selecting the taps is achieved by changing the value of <code>self.tsel</code> signal !

In the finished version of the project, the tap list is stored in the `.pickle` file so that there is no need to hard code these values that we are able to compute dynamically.

## Synchronizing the LFSR with the 1-PPS signal

### Detecting the 1-PPS signal rise

The 1-PPS signal can occur in 2 different ways:
- the 1-PPS is high shorter than a clock cycle of the FPGA
- the 1-PPS is high longer than a clock cycle of the FPGA


In the first situation, it is possible that we just miss the 1-PPS because it did not stay in the high state long enough for us to detect it with:
```python
with m.If(pps):
    m.d.sync += [
        # Do something
    ]
```
To avoid this kind of problem, a clock frequency that is high enough is selected so that the former case never happens (ie 630MHz in our case).

However, we can still manage the second situation. The risk here, would be that the `pps` signal is lasting more than one clock cycle making the previously suggested code execute several times instead of just once. The trick to overcome this problem is to _synchronously_ write down the value of the 1-PPS signal. When doing this, on the next rising edge of the FPGA clock, we can compare the old 1-PPS value with the new one. If they are different and the new one is high, then we just detected a rising edge of the 1-PPS :
```python
m.d.sync += old_pps.eq(self.pps)

with m.If( (old_pps ^ self.pps) & self.pps ):
	m.d.sync += [
		# some code that just has 
        # to be executed on the pps rising edge
	]
```

Great ! but not sufficient. Because of the FPGA architecture, it may happen that the rising edge of the pps is not clearly detected because by the time we synchronously check for the value of `old_pps ^ self.pps`, the value of old_pps may have changed ! This can happen because of the routing delay of the 1-PPS signal and the Flip-Flops that care about our signal. To make sure everything is finely computed, instead of directly working with the 1-PPS signal and the same signal synchronously captured, we will only work with Synchronously captured PPS with different delays (the PPS signal will get through several Flip-Flops before being processed :

```python
pps_1 = Signal()
pps_2 = Signal()
pps_old = Signal()
rise_pps = Signal()
m.d.sync += [
	pps_1.eq(PPS_SIGNAL_SOURCE),
	pps_2.eq(pps_1),
	pps_old.eq(pps_2)
]

m.d.comb += rise_pps.eq((pps_2 ^ pps_old) & pps_2)

```

This way, we really make sure there is no problem to detect the PPS rising edge. But you may think : "Hey ! but processing the signal AFTER having it getting through those FFs results in a delay between the moment we detect the PPS and the real moment the PPS rises!" And you're not wrong. But it is just fine since we know exactly how many clock rising edge to wait between the original signal and the one we process.

### Generation of the PRN triggered by the 1-PPS signal

To keep our code as modular as possible, we will prefer to develop separatly the implementation of the PRN generator and its synchronization with the 1-PPS.

In order for the LFSR to stop and run on demand, an `enable` signal is added in order to keep the LFSR in its initial state as long as `enable` remains in the low state. When it goes high, the LFSR starts generating the PRN.

So in the end, the elaborate method of our PrnGenerator looks like this:

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
		with m.If(self.enable==0):
			m.d.sync += [
				self.reg.eq(self.reg.reset)
			]

		return m
```

In this portion of code, we notice that there are 3 signals used in the LFSR that are not directly driven within its implementation. This means we will have to set ourself the values of `self.enable` and  `self.next` (and perhaps `self.tsel`) from _outside_ the class. Which is fine because we need to use our own prescaler as a `next` signal, and our 1-PPS rising edge as the deassertion condition for the `enable` signal.

### Making the PPS, Prescaler and LFSR cohabit

As we now have the Prescaler and the LFSR in two different classes, we may want to create a third module to merge them into a uniq module that is receiving a PPS and generating the PRN according to it. So it would only have one input signal (1-PPS) (or two inputs if the taps are dynamically chosen) and one output signal. I should also be parametrized with:
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
		pps_1 = Signal()
		pps_2 = Signal()
		pps_old = Signal()
		rise_pps = Signal()
		m.d.sync += [
			pps_1.eq(self.pps),
			pps_2.eq(pps_1),
			pps_old.eq(pps_2)
		]
		m.d.comb += rise_pps.eq((pps_2 ^ pps_old) & pps_2)
		
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

Next step: [Carrier signal generation](04_Carrier_Generation.md)
