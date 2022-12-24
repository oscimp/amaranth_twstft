# 5-day long TWSTFT transfer experiment

The objective of this experiment was to validate the long term synchronization
of emission and reception sequences, processing and storage. The huge amount
of data and the lengthy processing time are significant challenges, with a total
of nearly 690 GB generated over 5 days on each site. The Raspberry Pi 4 in Besancon
is unable to process in less than 30 minute at the moment a dataset so each
dataset was uploaded to a remote server (20 to 25 minute transfer duration) and 
remotedly processed using GNU/Octave (60 minute processing time for a ranging
and a two way processing).

## Processing language performance

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
Panasonic [CF19 MK8](https://www.bobjohnson.com/blog/a-note-on-model-numbers-for-toughbook-nerds/) 
laptop fitted with a Intel i5-3610ME CPU @ 2.70GHz. The sample file is a 5 second long, 
200 MB record.

| Processing time v.s language | Ranging     | Two-way    |
| ---------------------------- | ----------- |----------- |
| GNU/Octave [0]               | 58 s       | XXX s      |
| Python/numpy [1]             | 97 s       | XXX s      |
| Python/pyfft [2]             | 85 s (4 threads)/76 (1-thread)       | XXX s      |
| C++ [3]                      | 22 s       | XXX s      |
| C++ [3] on RPi4/performance  | 54 s       | XXX s      |

[0]
```
n      dt1     df1     P1      SNR1    dt2     df2     P2      SNR2
1      0.988264101405  1780.750        80.2    -5.2    0.725310892500  0.250   85.0    -1.2
2      0.988264097903  1780.750        80.2    -5.0    0.725310892496  0.250   85.0    -1.2
3      0.988264094808  1780.750        80.2    -5.1    0.725310892472  0.250   85.0    -1.2
4      0.988264091094  1780.750        80.1    -5.1    0.725310892466  0.250   85.0    -1.2
5      0.988264088312  1780.750        80.1    -5.1    0.725310892463  0.250   85.0    -1.2
```

[1]
```
0 	0.988264034738	1780.75	80.2	-5.2	0.725310774185	72.1	-0.8
1 	0.988264031236	1780.75	80.2	-6.0	0.725310774193	72.1	-0.8
2 	0.988264028141	1780.75	80.2	-6.0	0.725310774212	72.1	-0.8
3 	0.988264024427	1780.75	80.1	-6.0	0.725310774221	72.1	-0.8
4 	0.988264021646	1780.75	80.1	-6.0	0.725310774223	72.1	-0.8
```

[2]
```
0	0.988264034738	1780.75	80.2	-5.2	0.725310774185	72.7	0.6
1	0.988264031236	1780.75	80.2	-6.0	0.725310774193	72.7	0.6
2	0.988264028085	1780.381	80.2	-7.3	0.725310774212	72.7	0.6
3	0.988264024422	1780.651	80.1	-5.9	0.725310774221	72.7	0.6
4	0.988264021614	1780.298	80.1	-8.1	0.725310774223	72.7	0.6
```

[3]
```
file size : 5000000 5000000
0 0.988264034738	1780.750	 0.725310774166	0.250
1 0.988264031236	1780.750	 0.725310774171	0.250
2 0.988264028141	1780.750	 0.725310774194	0.250
3 0.988264024427	1780.750	 0.725310774201	0.250
4 0.988264021646	1780.750	 0.725310774204	0.250
```

## SDR data loss

This [UHD](https://files.ettus.com/manual/page_general.html) documentation explains that O and D
outputs means overflow, so that some data have been lost. If this data loss occurs on startup, since
recording starts before the actual signal transmission, no relevant information is lost. If this
happens during datastreaming, it might be that since both loopback and reception channel are referenced
to the same timescale, the dataloss will compensate but this remains to be assessed.

<img src="processing/dataloss.png">

The red vertical line indicates RPi4 reboot in an attempt to reduce packet loss, to no avail. It might
be that the usage of ramfs is excessive, with a 7.5 GB RAMdisk out of the available 8 GB, leading to
swapping and the need to restore RAM during the next acquisition.
