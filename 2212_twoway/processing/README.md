* check_correlation.m for assessing the validity of the collected data by
displaying the cross-correlation of the first few seconds
* godual_ranging.m for processing the full datasets collected and stored for post-processing
* gofinal.m for analyzing the processing results of godual_ranging.m

<img src="221203_final.png">

Computation time on an Intel i5-3610ME CPU @ 2.70GHz (5388 bogomips), data
loaded from onboard SSD mass storage:
```
$ time octave -q godual_ranging.m
real    45m30.112s
user    42m9.818s
sys     2m30.883s

$ time python3 ./godual_ranging.py
real    49m9.854s
user    44m56.770s
sys     3m48.403s
```
After removal of the excessive FFTs (commit 2f7527352ace6ae284142712e17fbb95745fe1fb):
```
$ time python3 ./godual_ranging.py
real	29m39.138s
user	27m17.220s
sys	2m11.091s
```

An attempty of using pyfftw, not supported by Buildroot but to assess the speed improvement
with ``godual_ranging_fftw.py``
:
```
real	25m6.907s
user	23m46.791s
sys	1m9.231s
```

Computation time on a Raspberry Pi4, data loaded through the USB3 bus from an
external mechanical hard disk requiring less than 2 minutes to cp from ramdisk
to non-volatile storage:
```
# time python3 ./godual_ranging.py  > result_RPi.txt
real   2h 23m 50s                                                              
user    1h 58m 30s                                                              
sys     24m 42.39s                                                              
```

It was verified that increasing interpolation (Nint>1) is inefficient (larger iFFT) 
and only leads to excessive noise on the result, so Nint=1 seems to be optimal.
