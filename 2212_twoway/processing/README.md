* check_correlation.m for assessing the validity of the collected data by
displaying the cross-correlation of the first few seconds
* godual_ranging.m for processing the full datasets collected and stored for post-processing
* gofinal.m for analyzing the processing results of godual_ranging.m

<img src="221203_final.png">

Computation time on an Intel i5-3610ME CPU @ 2.70GHz (5388 bogomips), data
loaded from onboard SSD mass storage:
```
$ time octave -q godual_ranging.m > octaveoutput.txt 

real    45m30.112s
user    42m9.818s
sys     2m30.883s

$ time python3 ./godual_ranging.py > pythonoutput.txt 

real    49m9.854s
user    44m56.770s
sys     3m48.403s
```

Computation time on a Raspberry Pi4, data loaded through the USB3 bus from an
external mechanical hard disk:
```
# time python3 ./godual_ranging.py  > result_RPi.txt

```
