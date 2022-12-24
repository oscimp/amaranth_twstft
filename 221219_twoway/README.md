# 5-day long TWSTFT transfer experiment

The objective of this experiment was to validate the long term synchronization
of emission and reception sequences, processing and storage. The huge amount
of data and the lengthy processing time are significant challenges, with a total
of nearly 690 GB generated over 5 days on each site. The Raspberry Pi 4 in Besancon
is unable to process in less than 30 minute at the moment a dataset so each
dataset was uploaded to a remote server (20 to 25 minute transfer duration) and 
remotedly processed using GNU/Octave (60 minute processing time for a ranging
and a two way processing).
