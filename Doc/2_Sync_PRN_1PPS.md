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

In radiology, it is rare that the default frequency of our FPGA board is exactly the one we want to use for our modulation. So we want to simulate the use of a slower clock... In other words, we need a _Prescaler_. A _Prescaler_ is an electronic block that generates a pulse on its output at regular interval. 

Maybe you know how to make one IRL, but you can also find an amaranth software version of one [here](../1PPS_Sync/Prescaler.py).

Then we will use this prescaler to cadence our PRN generation as its impulse will be the signal that drives the LFSR shift. Let's say our FPGA board's frequency is 10 MHz, if we want to execute an operation with a frequency 5 MHz, we would turn this kind of code :

```python
#shifting operation
m.d.sync += self.reg.eq(Cat(self.reg[1:],insert))
```

into this one :
```python
#Instanciating our prescaler
presc = Prescaler(10e6, 5e6)

#Same operation but it will only be triggered if the prescaler enables it
with m.If(presc.output):
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

With this implementation, as long as we built our instance of <code>PrnGenerator20</code> with no defined value for <code>taps</code>, we can change the taps we use just by changing the value of <code>self.tsel</code> signal !

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
To avoid this kind of problem, we will choose a clock frequency that is high enough so that it never happens.

however, we can still manage the second situation. The risk here, would be that the `pps` signal is lasting more than one clock cycle making the previously suggested code execute several times instead of just one. The trick to overcome this problem is to _synchronously_ write down the value of the 1-PPS signal. When doing this, on the next rising edge of the FPGA clock, we can compare the old 1-PPS value with the new one. If they are different and the new one is high, then we just detected a rising edge of the 1-PPS :
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

As we need to get the LFSR to stop and go on demand, we can add to it a `reset` signal that will keep the LFSR in its initial state for as long as `reset` is high.

So in the end, the elaborate method of our PrnGenerator looks like this :

```python
	def elaborate(self,platform):
		m = Module()

        #choosing taps dynamically if the user didn't specify it
		if(self._dynamic_tsel):
			m.d.comb += self._taps.eq(self._mem[self.tsel])

        #bit to be inserted into the LFSR when shifted
		insert = Signal() 

		m.d.comb += [
			insert.eq((self._taps & self.reg).xor()),
			self.output.eq(self.reg[0]),
		]

        #when the reset signal is high, the LFSR returns to its initial state
		with m.If(self.reset):
            #these operations must be driven in the synchronous domain
            #because thats where we defined the signals _cnt and reg first

            #but the fact it is not surrounded by 
            #  with m.If(self.enable):
            #makes it happen anytime inbetween two shiftings
			m.d.sync += [
				self._cnt.eq(self._cnt.reset),
				self.reg.eq(self.reg.reset)
			]
        
        #we use an Else statement because otherwise,
        #the code below would override the one above as it is also
        #defining the behavours of _cnt and reg
		with m.Else():

            #waiting for the tick of the prescaler 
            #(or anything else that is driving the enable signal)
			with m.If(self.enable):
				m.d.sync += [
					self.reg.eq(Cat(self.reg[1:],insert)),
					self._cnt.eq(self._cnt-1)
				]
				with m.If(self._cnt == 0):
					m.d.sync += [
						self._cnt.eq(self._cnt.reset),
						self.reg.eq(self.reg.reset)
					]


		return m
```

In this portion of code, we remark that there are 3 signals used in our LFSR that are not directly driven within the implementation of it. This means we will have to set ourself the values of `self.reset` and  `self.enable` (and perhaps `self.tsel`) from _outside_ the class. Which is fine because we need to use our own prescaler as an `enable` signal, our 1-PPS rising edge as the `reset` signal.

### Making the PPS, Prescaler and LFSR cohabit

As we now have the Prescaler and the LFSR in two different classes, we may want to create a third module to merge them into a uniq module that is receiving a PPS and generating the PRN according to it. So it would only have one input signal (1-PPS) and one output signal and would be parametrized with the frequency of the clock we use and the frequency of the PRN generation we want. 

Last detail we should talk about is the fact the PRN generation should stop every second if it doesn't receive a PPS. To do it, the only clock we can use to wait a second is the one we already use. So we will just add a counter that counts up to the frequency of this clock. 

If this is a 10 MHz clock, one second should last 10 million ticks. Whenever we reach this value, we stop counting, we reset the PRN and the Prescaler for as long we don't receive a PPS. When it comes, we enable the prescaler, we stop reseting the LFSR and restart counting up to 10 millions.

Such module could be defined in yet another class :

```python
class Synchronizer(Elaboratable):
	"""A module that generates a 20-bits PRN 
    synchronized with a 1-PPS Signal in input
    """

	def __init__(self, freqin, freqout):
		self.pps = Signal() #input signal
		self.output = Signal() #synchronized PRN
		self._freqin = freqin #clock frequency
		self._freqout = freqout #prn generation frequency
	
	def elaborate(self, platform):
		m = Module()

		cnt = Signal(32) #signal to count up to the frequency
		
        #remembering the last value of the pps signal
        old_pps = Signal()
        m.d.sync += old_pps.eq(self.pps)

        #calling the modules we defined separatly
		m.submodules.prn = prn = PrnGenerator()
		m.submodules.presc = presc = Prescaler(self._freqin, self._freqout)

        #linking the prescaler output to the PRN Generation 
		m.d.comb += prn.enable.eq(presc.output)

        #detecting the pps rising edge
		with m.If( (old_pps ^ self.pps) & self.pps ):
			m.d.sync += [
				cnt.eq(cnt.reset),
				prn.reset.eq(1),
				presc.enable.eq(0)
			]

        #as long as there is no rising edge
		with m.Else():
            #we specify that the PRN generation is ongoing
			m.d.sync += [
				prn.reset.eq(0),
				presc.enable.eq(1)
			]
			#as long as we haven't counted up to the clock frequency
			with m.If(cnt<self._freqin):
				m.d.comb += self.output.eq(prn.output)
				m.d.sync += cnt.eq(cnt+1)
            #otherwise, we stop the PRN generation
			with m.Else():
				m.d.comb += self.output.eq(0)
				m.d.sync += cnt.eq(cnt)
		
		return m
```

And here we are ! 

Next step : [Carrier signal generation](3_Clk_Generation.md)