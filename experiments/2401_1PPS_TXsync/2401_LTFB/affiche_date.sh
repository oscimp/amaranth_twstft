for i in local*; do nom=`echo $i | cut -c 13-22`;date -d @$nom ;done
