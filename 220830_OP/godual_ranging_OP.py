#!/usr/bin/env python3

import numpy as np
import struct
import array

fs = (5e6)
foffset=0
frange=8000
freq = np.linspace(-fs/2, (fs/2), num=int(fs), dtype=float)
k=np.nonzero((np.array(freq) < 2*(foffset+frange)) & (np.array(freq) > 2*(foffset-frange)))
k=k[0];
temps = np.array(range(0, int(fs))) / fs

def ranging(filename, prn_code):
    with open(prn_code, "rb") as fd:
        codeb = fd.read()
        print(codeb[0:20])
        code = list(codeb)
        code=np.repeat(code,2); # interpolate
        print(code[0:40]);
        code=code-np.mean(code);
        fcode=np.conj(np.fft.fft(code))

    p = 0
    df = []
    indice1_lst = []
    indice2_lst = []
    correction1 = []
    correction2 = []
    with open(filename, "rb") as fd:
        must_stop = False
        while(not must_stop):
            data = fd.read(int(fs) * 4 * 2)
            if len(data) != int(fs) * 4 * 2:
                break
            d = struct.unpack('{}h'.format(len(data)//2),data)
            d1 = np.array(d[0::4], dtype=complex)
            d1.imag = np.array(d[1::4])
            d2 = np.array(d[2::4], dtype=complex)
            d2.imag = np.array(d[3::4])
            d1 -= np.mean(d1)
            d2 -= np.mean(d2)

            d1_fft = np.fft.fftshift(np.abs(np.fft.fft(d1 * d1)))
            tmp = d1_fft[k].argmax()+k[0]
            tmp = freq[tmp]/2
            df.append(tmp)
            lo = np.exp(-1j * 2 * np.pi * tmp * temps)
            y = d1 * lo              # frequency transposition
            multmp1 = np.fft.fftshift(np.fft.fft(y) * fcode)
            multmp2 = np.fft.fftshift(np.fft.fft(d2) * fcode)
            interpolation1=np.concatenate( (np.zeros(len(y))+1j*np.zeros(len(y)) , multmp1, np.zeros(len(y))+1j*np.zeros(len(y))))
            interpolation2=np.concatenate( (np.zeros(len(d2))+1j*np.zeros(len(d2)) , multmp2, np.zeros(len(d2))+1j*np.zeros(len(d2))))
            multmp1 = np.fft.fftshift(interpolation1)
            multmp2 = np.fft.fftshift(interpolation2)
            prnmap01 = np.fft.ifft(multmp1)       # correlation with returned signal
            prnmap02 = np.fft.ifft(multmp2)

            indice1 = abs(prnmap01).argmax()      # only one correlation peak
            indice2 = abs(prnmap02).argmax()
            xval1 = prnmap01[indice1]
            xval2 = prnmap02[indice2]
            xval1m1= prnmap01[indice1-1]
            xval1p1 = prnmap01[indice1+1]
            xval2m1 = prnmap02[indice2-1]
            xval2p1 = prnmap02[indice2+1]

            correction1=((abs(xval1m1)-abs(xval1p1))/(abs(xval1m1)+abs(xval1p1)-2*abs(xval1))/2);
            correction2=((abs(xval2m1)-abs(xval2p1))/(abs(xval2m1)+abs(xval2p1)-2*abs(xval2))/2);
            
            indice1_lst.append(indice1+correction1)
            indice2_lst.append(indice2+correction2)
            print(str(p)+": "+str(indice1)+"+"+str(correction1)+" -- "+str(xval1))
            p += 1

ranging("17h05.bin","../amaranth_twstft/220706_TWSTFT/OP_prn22bpskcode0.bin")
