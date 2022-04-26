# Pseudo-Random Noise Generation

It's no surprise that the use electromagnetic waves is required if we want to use satellite communication. however, the nature of the information we share makes it not so easy to transmit. We want to share a frequency information. Which is basically just a signal that's repeated over and over again. But the fact that this information is being repeated AND carried by a periodic signal is complicating the task. It's as if we were to diferenciate a sinusoid to another one with a 2pi phase shift. In such case, how to make the difference between our 1-PPS signal and the same signal a few milliseconds later ?

The solution ? __Binary Phase Shift Keying__ (BPSK) modulation. 

This kind of modulation allows us to transmit binary informations through the phase of our carrier signal. Whenever a 0 turns into a 1 (and vice-versa), the modulation applies a $\pi$ phase shift. 

<img src="../figures/BPSK.png">

We want to use this method to create a 1-PPS signal. So we need to make sure that the information carried does not repeat itself. This way, the auto-correlation of the signal gives us a one when the phase shift is 0 and a close-from-zero value otherwise. Which implies that we are able to differenciate the begining of the signal and subsequently, distinguish our 1_PPS within the received signal.

