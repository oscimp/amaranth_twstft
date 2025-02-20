from enum import Enum
from math import log
import pickle
from os.path import exists
from math import ceil


#Here is a small amount of functions that are used to calculate, 
#store and retrieve adequat taps to generate maximum length PRN sequences

pickle_file = "../saved_taps.pickle" #the file used to store the taps

taps_dict = {} #the dict

def unary_xor(x):
    """if x == 0b0101101, returns 0^1^0^1^1^0^1"""
    res = x & 1
    for i in range(1,int.bit_length(x)):
        x=x>>1
        res ^= 1 & x
    return res

def nextstate(current, code,bit_len):
    """returns the next state of the LFSR 
    following its size(bit_len), the taps 
    (code) and its current state (current)"""
    bit = unary_xor(current & code)
    res = current >> 1
    res |= bit << (bit_len-1)
    return res

def m_seq_codes(bit_len, limit = 10):
    """generates (limit) codes which binary values 
    represent where to put the taps on an LFSR to 
    generate a m-sequence of (bit_len) bits values"""
    codes = []
    first = 0x1

    codes_to_test = [2*i +1 for i in range(ceil(pow(2,bit_len)/2))]
    print(f"Finding at most {limit} taps for a {bit_len} bits msequence... This may take a while...") 
    for code in codes_to_test:
        test = first

        for j in range((pow(2,bit_len)-2)) : 
            test = nextstate(test, code, bit_len)

            if (test == first or test == 0):
                break


        if (test != first and test !=0):
            print(f"{code} is a m-sequence generator taps")
            codes.append(code)
            limit-=1
            if limit == 0 :
                break
    return codes

def write_prn_seq(bitlen, noiselen, taps_a, taps_b=None):
    """creates files with the PRN sequences associ  ated to the parameters"""
    filename = f'prn{taps_a}{f".{taps_b}q" if taps_b else "b"}psk{bitlen}bits.bin'
    with open(filename,"wb") as f:
        a = 1
        b = 1
        print(f"writing {'Q' if taps_b else 'B'}PSK sequence")
        for i in range(noiselen):
            f.write((a%2).to_bytes(1,byteorder='big'))
            a = nextstate(a, taps_a, bitlen)
            if taps_b:
                f.write((b%2).to_bytes(1,byteorder='big'))
                b = nextstate(b, taps_b, bitlen)
        f.close()
    print(f"see {filename}")

def taps_autofill(bit_len, nbtaps,save_file=pickle_file):
    global taps_dict
    if (bit_len in taps_dict and nbtaps <= len(taps_dict[bit_len])) :
        print(f"{bit_len} bits taps already saved)")
        return
    if exists(save_file) :
        with open(save_file,"rb") as f:
            taps_dict = pickle.load(f)
            f.close()
            if bit_len in taps_dict :
                if nbtaps <= len(taps_dict[bit_len]) :
                    print(f"{bit_len} bits taps already saved")
                    return

    taps = m_seq_codes(bit_len,nbtaps)
    set_taps(bit_len, taps, save_file = save_file)


def set_taps(bit_len,taps, save_file=pickle_file):
    global taps_dict
    print("Checking for saved taps...")
    if exists(save_file) :
        with open(save_file,"rb") as f:
            taps_dict = pickle.load(f)
            print("checking for taps existence")
            if bit_len in taps_dict :
                if len(taps) > len(taps_dict[bit_len]):
                    print(f"Updating {bit_len} bits taps.")
                    taps_dict[bit_len] = taps
                else :
                    print(f"Nothing to do, there are saved taps for {bit_len} bits already.")
            else :
                print(f"Adding {bit_len} bits taps to the taps dictionary.")
                taps_dict[bit_len] = taps
            f.close()
    else :
        print(f"No {save_file}, creating one")
        taps_dict[bit_len] = taps
    
    with open(save_file, 'wb') as f:
        pickle.dump(taps_dict,f)
        f.close()

def get_taps(bit_len,save_file=pickle_file):
    global taps_dict
    if bit_len in taps_dict :
        return taps_dict[bit_len]
    if exists(save_file) :
        with open(save_file,"rb") as f:
            taps_dict = pickle.load(f)
            f.close()
            if bit_len in taps_dict :
                return taps_dict[bit_len]
    print(f"No taps found for {bit_len} bits ")
    return []




# Enum classes

class CalibrationMode(Enum):
    AUTO = 0
    CLK = 1
    PPS = 2
    OFF = 3

TIMECODE_SIZE = 6

class TimeCoderMode(Enum):
    OFF = 0
    INVERT_FIRST_CODE = 1
    TIMECODE = 2 # also invert first code

class Mode(Enum):
    OFF = 0
    CARRIER = 1
    BPSK = 2
    QPSK = 3

class SerialInCommands(Enum):
    TIMECODER_OFF = 0
    TIMECODER_INVERT_FIRST_CODE = 1
    SET_TAPS_A = 2
    SET_TAPS_B = 3
    MODE_CARRIER = 4
    MODE_BPSK = 5
    MODE_QPSK = 6
    MODE_OFF = 7
    SET_TIME = 8
    TIMECODER_TIMECODE = 9
    CALIB_OFF = 10
    CALIB_CLK = 11
    CALIB_PPS = 12
    CALIB_AUTO = 13

class SerialOutCodes(Enum):
    NOTHING = 0
    PPS_GOOD = 1
    PPS_EARLY = 2
    PPS_LATE = 3
    SERIAL_RX_OVERFLOW_ERROR = 4
    SERIAL_RX_FRAME_ERROR = 5
    SERIAL_RX_PARITY_ERROR = 6
    UNKNOWN_COMMAND_ERROR = 7
    CODE_UNALIGNED = 8
    SYMBOL_UNALIGNED = 9
    OSCIL_UNALIGNED = 10
    CALIBRATION_DONE = 12
