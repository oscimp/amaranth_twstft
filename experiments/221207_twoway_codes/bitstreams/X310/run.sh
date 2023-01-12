#!/bin/bash
#length   bitlen  tapsOParis  tapsLTFBesancon
#5000       13       39          27
#10000      14       57          43
#25000      15       17           3
#100000     17       15           9
#250000     18       63          39
#500000     19       63          39
#2500000     22      57           3

NOISELEN_LST=('5000' '10000' '25000' '100000' '250000' '500000' '2500000')
BITLEN_LST=('13' '14' '15' '17' '18' '19' '22')
TAPS_LST=('39' '57' '17' '15' '63' '63' '57')

for i in $(seq 0 6); do
	n=${NOISELEN_LST[$i]}
	b=${BITLEN_LST[$i]}
	t=${TAPS_LST[$i]}
	make clean
	make cleanall
	make X310_HG NOISELEN=$n BITLEN=$b TAPS=$t
	extension=noiselen${n}_bitlen${b}_taps${t}
	mkdir $extension
	prn_seq_name=prn${t}bpsk${b}bits.bin
	cp build/usrp_x310_fpga_HG.bin $extension/usrp_x310_fpga_HG_${extension}.bin
	cp build/usrp_x310_fpga_HG.bit $extension/usrp_x310_fpga_HG_${extension}.bit
	cp $prn_seq_name $extension/prn${t}bpsk${b}bits${n}.bin
done
