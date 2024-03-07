# Updated experiment with continuously streaming X310

Since we observe that the X310 drifts by a few ns during the first
minutes of acquisition, we continuously sample on both X310 Basic RX
channels, stream on a ZeroMQ Publish socket, and only collect data when
needed:
1. <a href="zmq_rx_short.grc">zmq_rx_short.grc</a> leads to 
<a href="zmq_rx_short.py">zmq_rx_short.py</a> executed in one terminal, 
running continuously. The graphical output helps checking that the 
datastream has not stopped.
2. <a href="crontab">crontab</a> launching the acquisition twice every
odd UTC hour, and possibly processing during the even hour, by executing ...
3. ... <a href="gosampling.sh">gosampling.sh</a>, which should only run for
the duration of the acquisition as determined by the number of samples in the
Head block. For testing purposes, <a href="gotest.sh">gotest.sh</a> acquires
fewer samples. The bash script call <a href="zmq_rx.grc">zmq_rx.grc</a>
and <a href="zmq_rx.py">zmq_rx.py</a> for the effective data collection.
4. <a href="log">log</a> demonstrates proper operation in the test phase.
