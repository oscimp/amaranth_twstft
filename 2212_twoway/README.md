# Zedboard

The Zedboard bitstreams were generated using
```bash
./flashZedBoard.py -t 43 --noiselen 10000 --bitlen 14
./flashZedBoard.py -t 27 --noiselen 5000 --bitlen 13
./flashZedBoard.py -t 3 --noiselen 25000 --bitlen 15
./flashZedBoard.py -t 9 --noiselen 100000 --bitlen 17
./flashZedBoard.py -t 39 --noiselen 250000 --bitlen 18
./flashZedBoard.py -t 39 --noiselen 500000 --bitlen 19
./flashZedBoard.py -t 3 --noiselen 2500000 --bitlen 22
```
and the bitstream is transfered to the Zedboard using the command
```
sudo openFPGALoader -b zedboard --freq 30e6 -m bitstream.bit 
```

Running ``openFPGALoader`` on the Raspberry Pi with its Buildroot generated
operating system involves
* installing libftdi1, libgpiod, and hidapi from Buildroot
* using rsync to update the image on the Raspberry Pi with the additional
files generated when compiling these libraries
* from the Raspberry Pi:
```
rsync -aP $PC_IP:$BUILDROOT_LOCATION/output/target/usr/lib /usr/lib
rsync -aP $PC_IP:$BUILDROOT_LOCATION/output/target/usr/bin /usr/bin
```
* compiling openFPGALoader for the Raspberry Pi: on the PC
```
mkdir /tmp/rpi
cmake -DCMAKE_INSTALL_PREFIX:PATH=/tmp/rpi -DCMAKE_TOOLCHAIN_FILE=$BUILDROOT_LOCATION/output/host/share/buildroot/toolchainfile.cmake ../
make
make install
```
and from the Raspberry Pi:
```
scp -r $PC_IP:/tmp/rpi/* /usr
```

Transfering the bitstream from the Raspberry Pi to the Zedboard is achieved with
```
# openFPGALoader -b zedboard --freq 30e6 -m prn9bpsk17bits.bin
write to ram
Jtag frequency : requested 30.00MHz  -> real 30.00MHz 
Open file DONE
Parse file DONE
load program
Flash SRAM: [==================================================]
100.00%
Done
```

All bitstreams for the Zedboard are located in ``bitstreams/zedboard``, with the pinout documented
at <a href="../Doc/0_Installation.md">

# X310

Flashing the X310 with a new bitstream is achieved from a PC using
```
$ time openFPGALoader -b usrpx310 --freq 30e6 usrp_x310_fpga_HG_noiselen5000_bitlen13_taps39.bit 

Jtag frequency : requested 30.00MHz  -> real 30.00MHz 
Open file DONE
Parse file DONE
load program
Flash SRAM: [==================================================] 100.00%
Done

real    0m4,888s
user    0m0,228s
sys     0m0,332s
```

All bitstreams for the X310 are located in ``bitstreams/X310``, with the pinout documented
at <a href="../Doc/8_X310.md">
