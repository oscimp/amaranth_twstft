# Using Amaranth to implement TWSTFT Signal generation

Two Way Satellite Time and Frequency Transfer (TWSTFT) is a procedure that uses satellite comunication to share a time and a frequency information in the form of a specific electromagnetic impulse repeated exactly every second and a 2.5 MHz signal, both carried by a Radio-Frequency 70MHz signal.

The goal here is to implement this on an FPGA board.

To implement such communication, we will here make use of Python library _Amaranth_. It is a python package that allows to describe an FPGA architecture with a lot of python idioms that makes the task much easier than with other languages like Vivado or VHDL. This library gives us the possibility to manage signals and registers in a quite intuitive way. It also abstracts a lot of FPGA programming concepts that are not that interesting for us in the context of TWSTFT. 

In this documentation, you will find explanations behind the amaranth implementation of TWSTFT and the Amaranth source code associated :

0. [Installation guide for amaranth and cie](Doc/0_Installation.md):
if you never programmed on FPGA boards before, this may be useful for becoming familiar with the opensource toolchain used in this
project.

1. [PRN generation](Doc/1_PRN.md):
Pseudo Random Noise (PRN) generation for spreading the spectrum as needed for accurate timing and differenciating the emitters (CDMA)

2. [Synchronizing PRN with a 1-PPS signal](Doc/2_Sync_PRN_1PPS.md):
making the noise repeat exactly every second to create our 1 Pulse Per Second (1-PPS) signal

3. [Carrier signal generation](Doc/3_Clk_Generation.md):
creating the electromagnetic signal that will carry the information (intermediate frequency to be upconverted for a satellite link)

4. [Mixing Signals](Doc/4_Mixing_Signals.md):
mixing the carrier with our 1-PPS to share the frequency information

5. [Next level, QPSK modulation](Doc/5_another_modulation.md):
stepping up the PSK modulation to transmit twice as much information

6. [Demodulating the N-PSK modulated signal using GNU Radio](Doc/6_Demodulation.md):
steps needed to demodulate the phase-modulated signal using GNU Radio or GNU/Octave

7. [Conclusion of the project](Doc/6_Conclusion.md)
