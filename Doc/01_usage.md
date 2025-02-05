# Cmod A7 integration
Back to the [README](../README.md)
Previous step : [Installation of Amaranth and cie](00_Installation.md)

This section details how to flash the gateware and how to configure the FPGA via UART serial.

## bitstream generation

```
usage: flashZedBoard.py [-h] [--platform PLATFORM] [--bitlen BITLEN] [--noiselen NOISELEN] [-m MODFREQ] [-p] [-v]
                        [--no-build] [--no-load] [--flash] [--build-dir BUILD_DIR] [--conv-to-bin]
                        [--toolchain TOOLCHAIN]

options:
  -h, --help            show this help message and exit
  --platform PLATFORM   Target Platform (cmoda7 only for now)
  --bitlen BITLEN       number of bits of the LFSR
  --noiselen NOISELEN   length of the PRN sequence
  -m MODFREQ, --modfreq MODFREQ
                        frequency of the PSK modulation (Herz) (default :2.5e6)
  -v, --verbose         prints all the parameters used for this instance of the program
  --no-build            sources generate only
  --no-load             don't load bitstream
  --flash               write bitstream into SPI flash (cmoda7 only)
  --build-dir BUILD_DIR
                        build directory
  --conv-to-bin         convert .bit file to .bit.bin
  --toolchain TOOLCHAIN
                        toolchain to use (Vivado or Symbiflow) (cmoda7 only) (default: Vivado)
```


```
./flashZedBoard.py --platform PLATFORM_NAME --bitlen=BITLEN --noiselen=NOISELEN --taps=TAPS
```

Requiered options:
- `BITLEN` is the *PRN* shift register size ([Pseudo-Random Noise generation](02_PRN.md)) (default: 17)
- `NOISELEN` is the number of bits produces before reseting the *PRN* shift register (default: 100000)

Optional options:
- `--no-build` limit to amaranth -> *verilog* convert
- `--no-load` bypass load step after bitstream 
- `--flash` write the bitstream in non-volatile memory, by default, the bitstream is writen to volatile memory.

for example:
```
./amaranth_twstft/flashZedBoard.py --bitlen 17 --noiselen 100000
```

**cmoda7 only**: by default *Vivado* is used to produces the bitstream, but it's
also possible to use the *f4pga* Open-Source toolchain.

## Pin functions


| function              | dir | <a href="https://digilent.com/reference/programmable-logic/cmod-a7/reference-manual">cmoda7</a> |
|-----------------------|-----|--------|
| 10MHz in              | in  | GPIO46 |
| PPS in                | in  | GPIO42 |
| calibration           | out | GPIO36 |
| output                | out | GPIO31 |
| UART-i                | in  | micro-USB |
| UART-o                | out | micro-USB |

Next step : [Pseudo-Random Noise generation](02_PRN.md)
