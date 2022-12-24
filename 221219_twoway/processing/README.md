# Results

The binary files streamed from the SDR were stored first in RAMdisk and then 
processed using godual_ranging.m and godual_ranging_remote.m (same script except
for the remote flag but allowing to run automatically the two processing sequence
in parallel from a crontab). The resulting Matlab files holding the relevant 
cross-correlation processing variables are kept for post-analysis using
verif.m (one for LTFB and one for OP since the naming conventions are different,
with the former prefixing the TwoWay analysis with remote and the latter using
a different sub-directory name). Below the result of post-analysis:

* ranging from LTFB

<img src="LTFB_LTFB.png">

* OP two-way seen from LTFB.

<img src="OP_LTFB.png">

* ranging from OP

<img src="OP_OP.png">
