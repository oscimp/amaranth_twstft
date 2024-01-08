cd /media/time/LaCie/timeraw
/usr/bin/octave -q /media/time/LaCie/timeraw/claudio_aligned_code_lo.m  &
/usr/bin/octave -q /media/time/LaCie/timeraw/claudio_aligned_code_re.m  &
/usr/bin/octave -q /media/time/LaCie/timeraw/claudio_aligned_code_ranging.m
sleep 300
gzip *mat
scp *mat.gz jmfriedt@65.21.30.42:/tmp/op
scp *m jmfriedt@65.21.30.42:/tmp/op
scp /home/time/scr* jmfriedt@65.21.30.42:/tmp/op
