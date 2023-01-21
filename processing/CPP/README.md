assumes the following development libraries are installed:

```
apt install build-essential libfftw3-dev libmatio-dev pkg-config libarmadillo-dev
```
and that https://sourceforge.net/projects/sigpack/ has been installed in the 
current directory.

The Makefile accepts one optional argument as variable ``FFTW_THREADS`` the number of
threads spawned by FFTW.

Execute
```
make
```
to compile: the resulting executable exepects at least two arguments: the 
binary file to be processed (16-bit complex integers) and the code (8-bit 
integers), whether the remote station is being decoded (1, avoids the unnecessary
processing of the loopback signal with the remote code) or the local
signal (0, correlates both the loopback and received signals with the local
code for reference timescale and ranging) and finally the frequency offset.
