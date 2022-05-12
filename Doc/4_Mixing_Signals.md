# Mixing our Carrier Signal with the 1-PPS Signal

Good news : We are almost done with our BPSK emission !
Once we get a proper signal to carry our information, we need to mix it with the PRN we emit. 
But here is another problem. 
To ensure that the signal can correctly be demodulated, we should care about the moment when the modulation is applied. We want the carrier signal to be phase-shifted only when it goes throug a zero value. This allows to keep the signal consistent. 

<img src="../figures/BPSKCorrect.png">

But how do we actually modulate our carrier signal ? Well, now that we are talking about it, there are two possibilities :
- modulating it physically through the use of a mixer,
- modulating it electronically with FPGA programmation.

Here, we'll focus on the second method.

the thing is, we have two signals : one to be modulated, and on to modulate with. From the point of view of amaranth programming, these signals can just take two values, zero and one. So our sinusoidal signal looks more like a square one. And the advantage of such signals is that they can easily phase shifted. Indeed, to apply a 180° phase shift, you only need to negate the value of the signal. So everytime the PRN value goes from one to zero and vice versa, we will reverse the bits of our carrier signal. How to do it ? With an `exclusive or` :

```python
elaborate(self, platform):
	m = Module()
	# In this example and the following one, 
	# we'll assume we have at disposal 
	# the carrier signal, the 1-PPS Signal and the 
	# Synchronizer module we decribed in the previous 
	# sections of this documentation
	pps_i = Signal()
	output = Signal()
	prn = Synchronizer(self.freqin, self.freqout)
	m.d.comb += prn.pps.eq(pps_i)
	
	# Mixing operation
	m.d.sync += output.eq(prn.output ^ carrier)
```


To make sure the phase transition happens at the moment the sinusoid goes by zero, we are going to use the same trick as the one for the 1-PPS detection, but this time, we are not only going to focus on the rising edge but also on the falling edge.


```python
old_carrier = Signal()
zero = Signal()

m.d.sync += old_carrier.eq(carrier)
m.d.comb += zero.eq(old_carrier ^ carrier),

with m.If(zero):
	m.d.sync += output.eq(prn.output ^ carrier)
```

And now we should be done for the modulation ! An example of a [Mixer program]('../Mixer/Mixer.py') is available in this directory. The last step is to choose on which pin to send the modulated signal, but we won't talk about it here as it depends a lot on the FPGA board you are using.



Previous step : [Generating the appropriate clock signal](3_Clk_Generation.md)
