# Generating our carrier signal
Back to the [README](../README.md)
Previous step: [mixing signals](05_Mixing_Signals.md)

We now have a very fine FPGA device producing a 70MHz carrier BPSK modulated for carrying the signal. What about doubling the amount of data transmitted with exactly the same bandwidth occupation?
We saw that having a zero and pi phase shift could allow us to represent binary information. But what about other phases? Instead of limitting ourself to only two values, why not using four? That would result in a {0, pi/2, pi, 3*pi/2} set of possible shifts.

Well... Let's do it ! Or... Can we ? having a 0 or pi phase shift to modulate our 70MHz binary signal is quite simple: it was just the same as inverting the output. But a binary signal cannot hold more than two different informations. If we want to create a modulable signal with four different states/phases, we are going to need a second signal. To make the difference between this second signal and the first one, we will need to have the second one in quadrature with the first one. 

So was born I/Q modulation. 

By modulating these signals separatly and summing the results, we obtain a new form of signal which we can phase shift with one of the {0, pi/2, pi, 3*pi/2} set of possible shifts. 
See it as a sum of a sine and cosine functions with the same frequency and same amplitude (70MHz in our case). In the end, we obtain another sinusoid with the same frequency. We will only need to separatly phase-shift one or another or both signals with the usual 0 or pi phase-shift to produce the 4 different states we intend to recreate !

Next step: [Demodulation](07_Demodulation.md) 
