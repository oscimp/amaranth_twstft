LD_LIBRARY_PATH=/usr/local/lib
cd /home/time/workarea/twstft-tools/scripts/operational/
sleep 40


ladate=$(date +'%s')
mjd=$(($ladate/86400+40587))

echo $ladate
echo $mjd
echo "Start"
logfile=/home/time/Documents/timelog/$ladate.$mjd.log
/usr/bin/python3 ../../grc/x310_acq.py > $logfile 2>&1 &
sleep 10
echo "relay1toggle tx on"
##/usr/bin/bash ./relay1toggle.sh
echo "waiting"
wait
echo "relay1toggle tx off"
##/usr/bin/bash ./relay1toggle.sh
echo "Done!"
# enregistrement sur pc
#mv /home/time/Documents/timeraw/fichier /home/time/Documents/timeraw/$ladate.bin
# enregistrement sur disque externe
#datefin=$(stat -c "%Y" /home/time/Documents/timeraw/fichier)
# Modif pour avoir la datation en ms dans le nom de fichier
datefin=$(stat -c "%Y" /home/time/Documents/timeraw/fichier).$(stat -c "%y" /home/time/Documents/timeraw/fichier | cut -d\. -f2 | cut -d\  -f1)
binfile=/home/time/Documents/timeraw/${ladate}_$datefin.bin
mv /home/time/Documents/timeraw/fichier $binfile
mv $binfile /media/time/LaCie/timeraw/  # JMF deplace de la fin du script ici 240104
sleep 1
#octave -q ./godual_ranging.m &
#octave -q ./godual_remote.m &
#wait
sleep 1
matfile=$ladate.$datefin.$mjd.mat
gzip /home/time/Documents/res/op/$matfile
gzip /home/time/Documents/res/remote/$matfile
##/usr/bin/python3 ./gofinal_OP.py
rm /home/time/Documents/res/op/$matfile
rm /home/time/Documents/res/remote/$matfile
#scp /home/time/Documents/res/op/$matfile.gz jmfriedt@jmfriedt.org:/home/jmfriedt/public_html/twstft/OP/res/op/
#scp /home/time/Documents/res/remote/$matfile.gz jmfriedt@jmfriedt.org:/home/jmfriedt/public_html/twstft/OP/res/remote/
cp $logfile /media/time/LaCie/timelog/
exit 0
