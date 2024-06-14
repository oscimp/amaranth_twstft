### 1 PPS output monitoring

1 PPS input v.s 1 PPS output after resynchronization with the FPGA internal
clock (synchronous process) and 1 PPS generated from the internal counter
(called 1PPS_out2 in the documentations).

Make sure to synthesize with the ``--debug`` option to output 1 PPS debug
signals.
