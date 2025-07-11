C++ data acquisition from two BasicRX fitted in an X310 connected by a 10 Gb
Ethernet interface. The associated crontab and data acquisition script (assumes
``/usr/bin/nice`` is suid root) provided as well to automate acquisition.

<img src="setup.png">

Broadcasting the signal is controlled by a Raspberry Pi4 triggered every second
with a 1-PPS input and NTP synchronized: the ``script_raspberryPi4.py`` script controls
the emission time and duration. 

Recording the X310 stream is performed through a 10 GbEthernet link to a PC storing on 
SSD: make sure to regularly
``sudo fstrim -v /data`` where ``/data/`` is the SSD mouting point and mount with
``lazytime,norelatime,noatime`` to reduce file access load. The data storage medium
is formatted as EXT2 filesystem to avoid journaling.

When updating to a new environment, make sure to
* update the working directory ``rep`` in goprocess.sh and gosampling.sh
* update the working directory (``datalocation='./'``) and code directory
(``codelocation='...'``) in all the Octave files
* update the speaker (``OP=0`` for LTFB or ``OP=1`` for OP)
* update the reference and surveillance channels (``remotechannel=2`` or ``remotechannel=2``
with ``localchannel=3-remotechannel``)
* update the working directory at the end of the Octave script when moving the processed files
