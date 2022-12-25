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

Notice the signal drop from OP at the middle of the session due to a damaged 
buffer. The SNR measurement at OP and LTFB confirms the power drop by 15 dB 
also observed on the emitter monitoring power probe. OP ranging standard deviation
is in the 200 ps range integrated over 2 minutes, LTFB exhibits some local
fluctuations in the ns range in the beginning and then settles to 200 ps standard
deviation as well. The frequency shift introduced by the satellite transponder
is consistent with 200 Hz fluctuations overs 5 days. The power emitted from LTFB
remained constant and so did its SNR measurement. The OP drop of SNR by 15 dB is
matched with a rise of its ranging standard deviation to about 1 ns.

# C++ application

Compiled with ``make`` if host and target are the same (e.g. x86 PC) or
``make FFTW_THREADS=0`` for single-threaded application (default), or
``make FFTW_THREADS=1`` for activating multi-threading.

For cross-compiling to the RPi4, assuming Buildroot is located in ``$BR``:
```
make BR_DIR=$BR CROSS_COMPILE=aarch64-linux-
```
which expects FFTW3 with double precision to be active in BR (as well as matio and libz).

The application expects two arguments, respectively the data file (interleaved complex
short integers) and the code sequence (unsigned 8-bit integers).

# Algorithm

The processing sequence is summarized as follows:

<img src="algo.png">

# Alignement

The final result of the Two-Way exchange is to compare the timestamps of the correlation
peaks at the two ends of the link. Such a comparison requires a common timescale between
the two datasets, which is not obvious since the two speakers are at different locations.
The proposed solution according to the following recording sequence

<img src="alignement.png">

is as follows:
* on both ends of the link, the processing script is started with a second resolution by
a crontab synchronized on NTP. The time needed to start the shell script is unknown but in
the second range
* on both ends of the link, the software defined radio is started. It is known that the
X310 starts faster than the B210, and that both need less than 10 seconds to start
* once the SDR launch sequence is started, a delay of 10 seconds is started. Each SDR
will take an unknown amount of time, assumed to be less than 10 seconds, to start
collecting data. Hence, the time scale on both ends start at different unknown times
noted t(OP) and t(LTFB)
* at some point, both speakers start emitting, at different start time due to the unknown
shell script execution latency
* from the GNU Radio acqusition script, it is known that both speakers transmit the exact same
duration (determined by the number of collected samples). 

The proposed alignement procedure is as follows (implemented in gofinal.m):
* LTFB has timestamped the exact (within 1 s) emission start time
* LTFB has recorded the ranging date as detected from a sharp rise in the SNR. This timestamp
is recorded as T
* OP has received the signal transmitted by LTFB with a delay equal to more or less the
ranging delay, both OP and LTFB being in Europe and at a similar view angle from the satellite.
Hence, the reception by OP of the signal transmitted by LTFB is known to be timestamped at T,
allowing to align both timescales
* All timescales -- LTFB ranging, OP ranging and OP TW -- are aligned on the common signal 
transmitted by LTFB and received as ranging by LTFB and TW by OP.

The resulting TW exchance analyzed this way is shown below:

<img src="tw_final.png">

