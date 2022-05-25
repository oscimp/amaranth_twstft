# Generating our carrier signal
Back to the [README](../README.md)
Previous step : [Synchronizing ](2_Sync_PRN_1PPS.md)

The idea now is to create our Radio Frequency signal. It should then have a good enough frequency to fit our emmission conditions.
In the rest of this chapter, we'll focus on how to recreate a 70 MHz signal (Why 70 ? Well... Why not ?) with our FPGA board.

## Creating a nice sinusoid

This 70 MHz signal that we want to recreate should look like a sinusoid. Our board only is capable of outputting zeros and ones (so this is a square signal). So the FPGA only is not enough to generate a nice and clean 70MHz signal and we will make use of a 70MHz band-pass filter. As a square signal is just [a sum of sinusoids with a different frequencies](https://mathworld.wolfram.com/FourierSeriesSquareWave.html), using a band-pass filter will only keep the componnent of the signal that is sinusoidal and remove all the harmonics.

And now that the question of the waveform is solved, let's get started with what matters the most to us : generatinng a 70MHz signal.

## Generating a frequency acceptable signal

We are now facing 2 different situations :
- If the FPGA has a fast enough clockrate, we can generate a slower signal by regularly invert the output bit of our 70MHz signal. Let's say we have a 280MHz clocksignal, to get a 70MHz one, we should produce a new tick every 4 clock ticks. But in fact, if we want to have a 50% duty cycle, that means whe should invert our output bit every 2 clock ticks. Which leads us to :
```python
#Assuming we have a 280MHz clockrate

sig_140MHz = Signal() 
carrier = Signal() 
m.d.sync += sig_140MHz.eq(~sig_140MHz) #two times slowlier than the clockrate

with m.If(sig_140MHz):
	m.d.sync += [
		self.carrier.eq(~self.carrier0) #two times slowlier than the 140MHz signal -> 70MHz 
	]
```

- If the FPGA isn't fast enough at first but contains an internal PLL or MMCM, we can use it to define a new clocksignal that our sync domain will use. This way, we would just need to choose a clock frequency that is fast enough to allow us to relate to the first solution AND that is slow enough to let the FPGA time to complete each calculation on every clock cycle (we won't talk about this subject anymore as it is a quite advanced FPGA programming topic but if you want to learn more anyway, __Steve Kilts__ _Advanced FPGA Design Architecture, Implementation, and Optimization_ is a very good guide to solve this kind of issues). In our case, we are working with a _ZedBoard - Zynq SoC Development Board_ so the implementation described underneath can (and probably will) change if you are using a different board.

```python
# Here we are working with a 20MHz default clock frequency
# So we need it to be 14 times quicker

def elaborate(self,platform):
		m = Module()
		
		m.domains.sync = ClockDomain(reset_less=True)
	
		platform_clk = platform.request(platform.default_clk)
		base_clk_freq    = platform.default_clk_frequency
		
		# Now, we prefer to use the MMCM instead of the PLL 
		# because it allows us to align the input clock
		# and mmcm output phases (and this is a level of 
		# precision we expect when implementing TWSTFT)
		
		mmcm_clk_out     = Signal()
		mmcm_locked      = Signal()
		mmcm_feedback    = Signal()
	
		#Need to use a buffer in input and output of the MMCM so that
		#the skewness of the  system remains correct
		clk_input_buf    = Signal()
		m.submodules += Instance("BUFG",
			i_I  = platform_clk,
			o_O  = clk_input_buf,
		)
		
		# The VCO values must be between 800 and 1600 MHz 
		# so we need to multiply the input clock (20MHz) 
		# such as the result falls into this range
		vco_mult = 42.0 " # 20*42 = 840 MHz
		mmc_out_div = 3.0  # 840 / 3 = 280 MHz
		mmc_out_period = 1e9 / (base_clk_freq * vco_mult / mmc_out_div) #nano seconds
				
		m.submodules.mmcm = Instance("MMCME2_BASE",
			p_BANDWIDTH          = "OPTIMIZED",
			p_CLKFBOUT_MULT_F    = vco_mult, 
			p_CLKFBOUT_PHASE     = 0.0, 
			p_CLKIN1_PERIOD      = int(1e9 // base_clk_freq), # 20MHz
			
			
			p_CLKOUT0_DIVIDE_F   = mmc_out_div,
			p_CLKOUT0_DUTY_CYCLE = 0.5,
			p_CLKOUT0_PHASE      = 0.0, #Align mmcm output phase with clock input
			
	
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
		
		clock_freq = 1e9/mmc_out_period
		
		
		#Finishing the implementation of our carrier signal generation...
```

But there is one last thing we should care about before talking about modulating this signal. 

## Changing the clock source

The thing is, we don't want to use the FPGA board embedded clock signal. It is unlikely that it is as precise as the atomic clock we use for our TWSTFT project 
so maybe we could use an external signal from this same atomic clock. And in order to do this, you should look at the amaranth configuration that we used to flash programs into the FPGA.

These configurations files are the one you find in the amaranth-boards repository.

Once you found the one that corresponds to your board, look at the i/o available for your device. In our case, several GPIO are available and, by reading the documantation associated to our ZedBoard, we find that only the A-labelled GPIO is clock capable, so this is the one we will use to replace the FPGA internal clock.

To reference this GPIO, the configuration file of the board gives us the following lines :

```python
class ZedBoardPlatform(XilinxPlatform):
    device = "xc7z020"
    package = "clg484"
    speed = "1"
    default_clk = "clk100"
    
    resources = [
        Resource("clk100", 0, Pins("Y9", dir="i"),
                 Clock(100e6), Attrs(IOSTANDARD="LVCMOS33")),

        Resource("userclk", 0, Pins("AA9", dir="i"), # pmoda.4
                 Clock(20e6), Attrs(IOSTANDARD="LVCMOS33")),
        
        # plus some other resources that we don't care about
    ]
    
    connectors = [
        Connector("pmoda", 0, "Y11 AA11 Y10 AA9 - - AB11 AB10 AB9 AA8 - -"),
        Connector("pmodb", 0, "W12 W11  V10 W8  - - V12  W10  V9  V8  - -"),
        Connector("pmodc", 0, "AB7 AB6  Y4  AA4 - - R6   T6   T4  U4  - -"),
        Connector("pmodd", 0, "V7  W7   V5  V4  - - W6   W5   U6  U5  - -"),
    ]
```

You may change the ```default_clk``` attribute of the class but it is not a very portable behavour and we'll much prefer to use the following solution :

Inside the ```elaborate``` method that we wish to flash on the FPGA, you can instanciate an object called a Resource. It will refer to any one of the Resources described in the config file (may the resource be a button, a led, a switch or a GPIO). 

In this case, to reference the pin on which we are going to plug our new clock, we will add the ressource to the platform argument this way :

```python
#following the config file extract above, 
#this is the parameter we should use to reference "userclk"
conna = ("pmoda",0) 

platform.add_resources([
		Resource('external_clk', 0,
			Subsignal('A4_i', 
				Pins('4', # the AA9 pin is the 4th one described in the connector list of pmoda 
					conn=conna,
					dir='i')),
			Attrs(IOSTANDARD="LVCMOS33"))
		])

new_clk = platform.request('external_clk',0)

#and from now on, we can access the input signal of the GPIO through
#		new_clk.A4_i
# So now we can instanciate our MMCM with :

m.domains.sync = ClockDomain(reset_less=True)
	
platform_clk = new_clk.A4_i
base_clk_freq = 20000000 #20 MHz signal

# etc... finishing the implementation of the elaborate method...
```



Next step : [Mixing this signal with the 1-PPS Signal](4_Mixing_Signals.md) 
