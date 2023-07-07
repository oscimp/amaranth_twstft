# Zedboard / PynqZ2 / cmod A7 integration
Back to the [README](../README.md)
Previous step : [Installation of Amaranth and cie](00_Installation.md)

*flashZedBoard* common script

```
usage: flashZedBoard.py [-h] [--platform PLATFORM] [--bitlen BITLEN]
                        [--noiselen NOISELEN] [--no-reload] [-s SEED]
                        [-t TAPS] [-m MODFREQ] [--invert-first-code]
                        [--no-invert-first-code] [--no-uart] [-p] [-v]
                        [--no-build] [--no-load] [--flash]
                        [--build-dir BUILD_DIR] [--conv-to-bin] [--debug]

options:
  -h, --help            show this help message and exit
  --platform PLATFORM   Target Platform (pynq, cmoda7, zedboard(default)
  --bitlen BITLEN       number of bits of the LFSR
  --noiselen NOISELEN   length of the PRN sequence
  --no-reload           stop generation after noiselen bits
  -s SEED, --seed SEED  initial value of the LFSR (default 1)
  -t TAPS, --taps TAPS  taps positions for the LFSR (if not defined, allows to
                        dynamically define taps (currently not supported so
                        default taps will be the smallest msequence generator
                        taps))
  -m MODFREQ, --modfreq MODFREQ
                        frequency of the PSK modulation (Herz) (default
                        :2.5e6)
  --invert-first-code   deprecated: default behaviour. Use --no-invert-first-
                        code to disable xoring + counter
  --no-invert-first-code
                        disable invert (xor) the first code after PPS rise and
                        8bits counter
  --no-uart             disable uart request for PC second sent during
                        sequence 1 -> 9 (cmoda7 only
  -p, --print           creates a binary file containing the PRN sequence that
                        should be generated
  -v, --verbose         prints all the parameters used for this instance of
                        the program
  --no-build            sources generate only
  --no-load             don't load bitstream
  --flash               write bitstream into SPI flash (cmoda7 only)
  --build-dir BUILD_DIR
                        build directory
  --conv-to-bin         convert .bit file to .bit.bin
  --debug               enable test signals
  --toolchain TOOLCHAIN
                        toolchain to use (Vivado or Symbiflow) (cmoda7 only) (default: Vivado)

```

## bitstream generation

```
./flashZedBoard.py --platform PLATFORM_NAME --bitlen=BITLEN --noiselen=NOISELEN --taps=TAPS
```

Where:
- `PLATFORM_NAME` may be `zedboard`, `pynq` or `cmoda7`
- `BITLEN` is the *PRN* shift register size ([Pseudo-Random Noise generation](02_PRN.md)) (default: 17)
- `NOISELEN` is the number of bits produces before reseting the *PRN* shift register (default: 100000)
- `TAPS` is the *PRN* taps to use (see [Pseudo-Random Noise generation](02_PRN.md))
  (if this argument is not provided,
  the first taps according to `BITLEN` is used) (default: None, 9: LTFB, 15:
  SYRTE)

Optional options:
- `--no-build` limit to amaranth -> *verilog* convert
- `--no-load` bypass load step after bitstream 

for example:
```
./amaranth_twstft/flashZedBoard.py --platform cmoda7 --bitlen 17 --noiselen 100000 -t 9 -p
```

**Note**: by default a numeric message (9bits) is sent once by second: the first
sequence is inverted, 8 next sequences are xored with a 8 bits internal counter
(LSB). This counter is free running, set to 0 after *enable* is set, incremented at each
PPS rising edge for *zynq* based boards and for *cmoda7* when `--no-uart` is passed to
*flashZedboard.py*. For cmoda7, for default behaviour: counter is set to 60,
never incremented until PC answer to the date request (once per second).
Communication is done using second FTDI interface, UART mode, 9600 8n1 (see
[this script](../amaranth_twstft/host_req_date.py) as an example).

To completely disable this coounter and the xor, `--no-invert-first-code` must
be used.

**cmoda7 only**: by default when `--no-load` is not passed to the script,
bitstream is loaded to volatile memory (configuration is lost after a power
cycle). But it's possible to write bitstream into non-volatile memory (SPI
Flash) by using `--flash`.

**cmoda7 only**: by default *Vivado* is used to produces the bitstream, but it's
also possible to use the *f4pga* Open-Source toolchain.

## Pin functions


| function              | dir | zedboard | pynq     | cmoda7 |
|-----------------------|-----|----------|----------|--------|
| 10MHz in              | in  | PMOD_A4  | RPI-11   | GPIO46 |
| PPS in                | in  | PMOD_C4  | RPI-32   | GPIO42 |
| enable                | in  | PMOD_C1  | RPI-8    | GPIO36 |
| output                | out | PMOD_D4  | RPI-3    | GPIO31 |
| BPSK/QPSK mode        | in  | SWITCH_0 | SWITCH_0 | GPIO23 |
| clean_carrier (debug) | in  | SWITCH_1 | SWITCH_1 | GPIO19 |
| clock out (debug)     | out | PMOD_B2  | RPI-15   | GPIO1  |
| PPS out (debug)       | out | PMOD_B3  | RPI-36   | GPIO3  |
| PPS out2 (debug)      | out | PMOD_B1  | RPI-40   | GPIO5  |
| mixer_o (debug)       | out | PMOD_B7  | RPI-20   | GPIO7  |
| mixer2_o (debug)      | out | PMOD_B8  | RPI-22   | GPIO9  |
| inv_prn (debug)       | out | PMOD_D2  | RPI-24   | GPIO11 |

### Zedboard

<img src="../figures/pinout_zedboard.png">

### CMOD A7

<img src="../figures/cmodA7_twtft.png">

### PYNQ Z2
The input and output signals are available on the 40-pin Raspberry Pi compatible header:

<img src="pynqz2_gpio_conn.png">

Next step : [Pseudo-Random Noise generation](02_PRN.md)
