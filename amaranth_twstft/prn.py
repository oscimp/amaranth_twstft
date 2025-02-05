#!/usr/bin/env python3

from amaranth import *
from amaranth.lib.wiring import Component, In, Out
from amaranth.sim import *
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

def write_prn_seq(bitlen, taps_a, taps_b=None):
    """creates files with the PRN sequences associ  ated to the parameters"""
    filename = f'prn{taps_a}{f".{taps_b}q" if taps_b else "b"}psk{bitlen}bits.bin'
    with open(filename,"wb") as f:
        a = 1
        b = 1
        print(f"writing {'Q' if taps_b else 'B'}PSK sequence")
        for i in range(bitlen):
            f.write((a%2).to_bytes(1,byteorder='big'))
            a = nextstate(a, taps_a, bitlen)
            if taps_b:
                f.write((b%2).to_bytes(1,byteorder='big'))
                b = nextstate(b, taps_b, bitlen)
        f.close()
    print(f"see f{filename}")

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


#default number of different taps to choose among when dynamically selecting the taps for the LFSR
nb_taps_auto = 32

class PrnGenerator(Component):
    """
        A LFSR with same-tick-action shift and reset.
        The taps and the seed can be modified at runtime.
    """
    def __init__(self, bit_len, taps=None, seed=1):
        assert bit_len > 1
        super().__init__({
            "reset": In(1),
            "shift": In(1),
            "taps": In(bit_len),
            "seed": In(bit_len),
            "state": Out(bit_len)
            })
        self.bit_len = bit_len
        self._taps = taps
        self._seed = seed

    def elaborate(self, platform):
        m = Module()

        reg = Signal(self.bit_len, reset_less=True)

        if self._taps is not None:
            m.d.comb += self.taps.eq(self._taps)

        if self._seed is not None:
            m.d.comb += self.seed.eq(self._seed)

        m.d.comb += self.state.eq(reg)

        with m.If(self.shift):
            insert = (reg & self.taps).xor()
            new_state = Cat(reg[1:], insert)
            m.d.comb += self.state.eq(new_state)
            m.d.sync += reg.eq(new_state)

        with m.If(self.reset):
            m.d.comb += self.state.eq(self.seed)
            m.d.sync += reg.eq(self.seed)

        return m

class PrnGeneratorTest(Simulator):
    def __init__(self):
        self.bit_len = 14
        self.taps = 3
        self.seed = 1
        self.dut = PrnGenerator(self.bit_len, self.taps, self.seed)
        super().__init__(self.dut)
        self.add_clock(1)
        self.add_testbench(self.test_pnr)

    async def test_pnr(self, ctx: SimulatorContext):
        ctx.set(self.dut.reset, True)
        assert ctx.get(self.dut.state) == self.seed
        await ctx.tick()
        ctx.set(self.dut.reset, False)
        for _ in range(5):
            assert ctx.get(self.dut.state) == self.seed
            await ctx.tick()
        state = self.seed
        for _ in range(5):
            ctx.set(self.dut.shift, True)
            state = nextstate(state, self.taps, self.bit_len)
            assert ctx.get(self.dut.state) == state
            await ctx.tick()
            ctx.set(self.dut.shift, False)
            assert ctx.get(self.dut.state) == state
            await ctx.tick()
            assert ctx.get(self.dut.state) == state
        ctx.set(self.dut.shift, True)
        for _ in range(5):
            state = nextstate(state, self.taps, self.bit_len)
            assert ctx.get(self.dut.state) == state
            await ctx.tick()
        ctx.set(self.dut.reset, True)
        assert ctx.get(self.dut.state) == self.seed
        await ctx.tick()
        ctx.set(self.dut.reset, False)
        ctx.set(self.dut.shift, False)
        assert ctx.get(self.dut.state) == self.seed

if __name__ == "__main__":
    PrnGeneratorTest().run()
