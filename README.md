# Using Amaranth to implement TWSTFT Signal generation

(We assume here that you have already installed Amaranth and all the tools required to use it with your FPGA board)

Two Way Satellite Time and Frequency Transfer (TWSTFT) is a procedure that uses satellite comunication to share a time and a frequency information in the form of a specific electromagnetic impulse repeated exactly every second

To implement such communication, we will here make use of Python library _Amaranth_. This library gives us the possibility to manage signals and registers in a quite intuitive way. It also abstracts a lot of FPGA programming concepts that are not that interesting for us in the context of TWSTFT. 

In this documentation, you will find explanations behind the amaranth implementation of TWSTFT and the Amaranth source code associated :

1. [PRN generation](PRN/1_PRN.md) :
Pseudo Random Noise generation that allows to differenciate signals

2. [Synchronizing PRN with a 1-PPS signal](1PPS/2_Sync_PRN_1PPS.md) :
Making the noise repeat exactly every second to create our 1 Pulse Per Second signal

3. [Carrier signal generation](Carrier/3_Clk_Generation.md) :
Creating the electromagnetic signal that will carry the information up to the satellite

4. [Mixing Signals](Mixer/4_Mixing_Signals.md) :
Mixing the carrier with our 1-PPS to share the frequency information