# 5-day long TWSTFT transfer experiment

The objective of this experiment was to validate the long term synchronization
of emission and reception sequences, processing and storage. The huge amount
of data and the lengthy processing time are significant challenges, with a total
of nearly 690 GB generated over 5 days on each site. The Raspberry Pi 4 in Besancon
is unable to process in less than 30 minute at the moment a dataset so each
dataset was uploaded to a remote server (20 to 25 minute transfer duration) and 
remotedly processed using GNU/Octave (60 minute processing time for a ranging
and a two way processing).

In order to overcome the remote signal processing limitation, four versions of
the processing software have been investigated:
* GNU/Octave, most intuitive for a programmer familiar with the Matlab framework,
but not available on Buildroot/Raspberry Pi 4 and too slow any way since being
single threaded
* Python3 with the numpy FFT: available on Buildroot and RPi4, but single threaded
and slower than GNU/Octave
* Python3 with pyfft: faster, but pyfft is not available on Buildroot
* C++

All these versions must be validated on unit tests to assess the consistency of their
result and the computation duration associated with each language on a common platform.
Since GNU/Octave is not available on the Raspberry Pi4, the selected platform is a 
Panasonic CF19 Gen7 laptop fitted with a Intel i5-3610ME CPU @ 2.70GHz.

| Processing time v.s language | Ranging     | Two-way    |
| ---------------------------- | ----------- |----------- |
| GNU/Octave                   | XXX s       | XXX s      |
| Python/numpy                 | XXX s       | XXX s      |
| Python/pyfft                 | XXX s       | XXX s      |
| C++                          | XXX s       | XXX s      |
