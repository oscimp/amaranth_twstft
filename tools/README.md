```
$ for i in `seq 0 100`; do ./mseq_calculator 17 $i;done | grep OK
17 9	-> 131071/131071 OK
17 15	-> 131071/131071 OK
17 33	-> 131071/131071 OK
17 45	-> 131071/131071 OK
17 51	-> 131071/131071 OK
17 63	-> 131071/131071 OK
17 65	-> 131071/131071 OK
17 85	-> 131071/131071 OK
```

or using the Python script in ``amaranth_twstft``:
```
$ python -i amaranth_twstft/common.py
>>> m_seq_codes(17, 5)
```
will return 17-bit LFSR tap position with at most 5 taps:
```
Finding at most 5 taps for a 17 bits msequence... This may take a while...
9 is a m-sequence generator taps
15 is a m-sequence generator taps
33 is a m-sequence generator taps
45 is a m-sequence generator taps
51 is a m-sequence generator taps
[9, 15, 33, 45, 51]
```
