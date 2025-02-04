 #!/usr/bin/env python

import serial
import vxi11
import math
import numpy as np
import matplotlib.pyplot as plt

from vxi11.vxi11 import time

from uart_wrapper import SerialOutCodes
from calibration_output import CalibrationMode
from twstft_config import monitor, new_empty_monitoring_handlers, new_serial, set_calib_mode

def find_instruments():
    synth = None
    oscil = None
    for ip in vxi11.list_devices():
        instr = vxi11.Instrument(ip)
        name = instr.ask('*IDN?')
        if '33220A' in name:
            print(f'found {name} @ {ip}')
            synth = instr
        if 'RTO' in name:
            print(f'found {name} @ {ip}')
            oscil = instr
        if synth and oscil:
            break
    return synth, oscil

def setup_oscil(oscil: vxi11.Instrument):
    oscil.write('TRIG:SOURCE CHAN1')
    oscil.write('TRIG:TYPE EDGE')
    oscil.write('TRIG:EDGE:SLOPE POS')
    oscil.write('TRIG:LEVEL 1') # trig at 1V

    oscil.write('SEARCH:ADD "PPS"') # define PPS SEARCH
    oscil.write('SEARCH:ONLINE "PPS",ON')
    oscil.write('SEARCH:SOURCE "PPS",C2W1')
    oscil.write('SEARCH:TRIG:TYPE "PPS",EDGE')
    oscil.write('SEARCH:TRIG:LEVEL "PPS",1')
    oscil.write('SEARCH:TRIG:EDGE:SLOPE "PPS",POS')
    oscil.ask('*OPC?')

def get_pps_offset(oscil):
    offset = float(oscil.ask('SEARCH:RES? "PPS"').split(',')[1])
    oscil.write('SEARCH:CLEAR "PPS"')
    return offset

def setup_synth(synth: vxi11.Instrument):
    synth.write('FUNC SIN')
    synth.write('FREQ 10e6')
    synth.write('VOLT:LOW -50e-3')
    synth.write('VOLT:HIGH 50e-3')
    synth.write('UNIT:ANGLE RADIAN')
    synth.write('PHASE 0')
    synth.write('OUTPUT ON')
    synth.ask('*OPC?')

def acquire(synth, oscil, steps=10, reps=10):
    setup_oscil(oscil)
    setup_synth(synth)
    s = new_serial('/dev/ttyUSB1')

    results = [[]]
    i = 0
    j = 0

    def pps_handler(s, code):
        nonlocal i, j
        time.sleep(0.2)
        offset = get_pps_offset(oscil)
        print(offset)
        if j == reps:
            i += 1
            j = 0
            results.append(list())
            synth.write(f'PHASE {2*math.pi*i/steps/28}')
        if i == steps:
            s.close()
            return
        results[i].append(offset)
        j += 1
    handlers = new_empty_monitoring_handlers()
    handlers[SerialOutCodes.PPS_GOOD].append(pps_handler)
    handlers[SerialOutCodes.PPS_EARLY].append(pps_handler)

    monitor(s, handlers)

    return results

def get_view(oscil: vxi11.Instrument):
    start, stop, size, _ = map(float, oscil.ask('CHAN1:DATA:HEADER?').split(','))
    size = int(size)
    ch1 = np.array(list(map(float, oscil.ask('CHAN1:DATA?').split(','))))
    ch2 = np.array(list(map(float, oscil.ask('CHAN2:DATA?').split(','))))
    x = [start+ i*(stop-start)/size for i in range(size)]
    plt.plot(x, ch1, label='PPS signal')
    plt.plot(x, ch2, label='PPS detected')
    plt.title('Oscilloscope capture in PPS signal calibration')
    plt.xlabel('Time [s]')
    plt.ylabel('Tension [V]')
    plt.show()

def show(results):
    steps = len(results)
    reps = len(results[0])
    span = lambda x: max(x) - min(x)
    x = [2*math.pi*i/steps for i in range(steps)]
    color = ['blue' if span(r) < 2e-9 else 'red' for r in results]
    plt.scatter(
            [[x]*reps for x in x],
            results,
            marker='.',
            c=sum(([c]*reps for c in color), start=[]))
    avg = [np.average(r) for r in results]
    std = [np.std(r) for r in results]
    plt.errorbar(x, avg, std, linestyle='None', marker='_', c='grey')#, c=['blue' if c == 'blue' else c for c in color]

    plt.axhspan(
            max(y for y in sum((r for r in results if span(r) > 2e-9), start=[]) if y < np.average(avg)),
            min(y for y in sum((r for r in results if span(r) > 2e-9), start=[]) if y > np.average(avg)),
            color = 'green',
            alpha = 0.5,
            )

    plt.title('Span of safe clock-to-PPS phase')
    plt.xlabel('Introduced phase on 280MHz [radian] (arbitrary zero)')
    plt.ylabel('PPS to PPS\'s detection delay [s]')

    plt.show()
