# Using Amaranth to implement TWSTFT Signal generation

Two Way Satellite Time and Frequency Transfer (TWSTFT) is a procedure that uses satellite comunication to share a time and a frequency information in the form of a specific electromagnetic impulse repeated exactly every second and a 2.5 MHz signal, both carried by a Radio-Frequency 70MHz signal.

The goal here is to implement this on an FPGA board.

To implement such communication, we will here make use of Python library _Amaranth_. It is a python package that allows to describe an FPGA architecture with a lot of python idioms that makes the task much easier than with other languages like Vivado or VHDL. This library gives us the possibility to manage signals and registers in a quite intuitive way. It also abstracts a lot of FPGA programming concepts that are not that interesting for us in the context of TWSTFT. 

In this documentation, you will find explanations behind the amaranth implementation of TWSTFT and the Amaranth source code associated :

0. [Installation guide for amaranth and cie](Doc/0_Installation.md) :
If you never programmed on FPGA boards before, this may be useful

1. [PRN generation](Doc/1_PRN.md) :
Pseudo Random Noise generation that allows to differenciate signals

2. [Synchronizing PRN with a 1-PPS signal](Doc/2_Sync_PRN_1PPS.md) :
Making the noise repeat exactly every second to create our 1 Pulse Per Second signal

3. [Carrier signal generation](Doc/3_Clk_Generation.md) :
Creating the electromagnetic signal that will carry the information up to the satellite

4. [Mixing Signals](Doc/4_Mixing_Signals.md) :
Mixing the carrier with our 1-PPS to share the frequency information
