#!/usr/bin/env python3

import numpy as np
import struct
import array
from datetime import datetime

fs = (5e6)
foffset=0
frange=8000
Nint=1
affiche=0
debug=0

if (affiche==1):
    import matplotlib.pyplot as plt

def processing(d1,k,freq,temps,fcode,code):
        interpolation1=np.zeros((Nint*2+1)*len(code))+1j*np.zeros((Nint*2+1)*len(code))  # prepare empty array for interpolation
        yint=np.zeros((2*Nint+1)*len(code))+1j*np.zeros((2*Nint+1)*len(code))
        d1_fft = np.fft.fftshift(np.abs(np.fft.fft(d1 * d1)))
        tmp = d1_fft[k].argmax()+k[0]
        df1tmp = freq[tmp]/2
        lo = np.exp(-1j * 2 * np.pi * df1tmp * temps)
        y1 = d1 * lo                             # frequency transposition
        a=np.polyfit(np.arange(1,fs//3,10)/fs,np.convolve(np.angle(y1[0:int(fs//3):10]),np.ones(100)/100)[49:-50],1)
        dfleftover1=a[0]/2/np.pi
        lo=np.exp(-1j*2*np.pi*dfleftover1*temps) # frequency offset
        y1=y1 * lo                               # fine frequency transposition
        df1tmp+=dfleftover1
        fft1tmp=np.fft.fft(y1)
        multmp1 = fft1tmp * fcode
#       interpolation1=np.concatenate( (np.zeros(len(y))+1j*np.zeros(len(y)) , multmp1, np.zeros(len(y))+1j*np.zeros(len(y))))     # Nint=1
        interpolation1[:len(y1)//2]=multmp1[:len(y1)//2]
        interpolation1[-len(y1)//2:]=multmp1[-len(y1)//2:]
#       multmp1 = np.fft.fftshift(interpolation1)
        prnmap01 = np.fft.ifft(interpolation1)   # correlation with returned signal
        indice1 = abs(prnmap01).argmax()         # only one correlation peak
        xval1 = prnmap01[indice1]
        xval1m1= prnmap01[indice1-1]
        xval1p1 = prnmap01[indice1+1]
        correction1=((abs(xval1m1)-abs(xval1p1))/(abs(xval1m1)+abs(xval1p1)-2*abs(xval1))/2);
        if debug==1:
            print(indice1)
            print(dfleftover1)
            print(xval1m1)
            print(xval1)
            print(xval1p1)
# SNR1 computation
#       yf = np.fft.fftshift(np.fft.fft(y))
#       yint = np.concatenate( (np.zeros(len(y))+1j*np.zeros(len(yf)) , yf , np.zeros(len(y))+1j*np.zeros(len(y))))  # Nint=1
#       yint=np.fft.ifft(np.fft.fftshift(yint))  # back to time /!\ outer fftshift for 0-delay at center
        yint[:len(y1)//2]=fft1tmp[:len(y1)//2]
        yint[-len(y1)//2:]=fft1tmp[-len(y1)//2:]
        yinti=np.fft.ifft(yint)
        codetmp=np.repeat(code,2*Nint+1)   # interpolate 2*Nint+1
        yincode=np.concatenate((yinti[indice1-1:] , yinti[:indice1-1]))*codetmp;
        SNR1r=np.mean(np.real(yincode))**2/np.var(yincode);
        SNR1i=np.mean(np.imag(yincode))**2/np.var(yincode);
        puissance1=np.var(y1)
        puissance1code=np.mean(np.real(yincode))**2+np.mean(np.imag(yincode))**2
        puissance1noise=np.var(yincode)
        return indice1,correction1,SNR1r,SNR1i,df1tmp,puissance1,puissance1code,puissance1noise

def ranging(filename, prn_code,foffset,remote):
    print(filename[0:10])
    ts = int(filename[0:10])

    with open(prn_code, "rb") as fd:
        codeb = fd.read()
        print(codeb[0:20])
        code = list(codeb)
        code=np.repeat(code,2)             # interpolate (ASSUMES 2.5 Mchips/2)
        print(code[0:40])
        code=code*2-1
        fcode=np.conj(np.fft.fft(code))
    freq = np.linspace(-fs/2, (fs/2), num=len(code), dtype=float)
    k=np.nonzero((np.array(freq) < 2*(foffset+frange)) & (np.array(freq) > 2*(foffset-frange)))
    k=k[0];
    temps = np.array(range(0, len(code))) / fs
    p = 0
    df1 = []
    df2 = []
    indice1_lst = []
    SNR1r_lst = []
    SNR1i_lst = []
    if remote==0:
        indice2_lst = []
        SNR2r_lst = []
        SNR2i_lst = []
        interpolation2=np.zeros((Nint*2+1)*len(code))+1j*np.zeros((Nint*2+1)*len(code))
    with open(filename, "rb") as fd:
        must_stop = False
        while(not must_stop):
            data = fd.read(len(code) * 4 * 2)
            if len(data) != len(code) * 4 * 2:
                break
            d = struct.unpack('{}h'.format(len(data)//2),data)
            d1 = np.array(d[0::4], dtype=complex)
            d1.imag = np.array(d[1::4])
            d1 -= np.mean(d1)
            indice1,correction1,SNR1r,SNR1i,df1tmp,puissance1,puissance1code,puissance1noise=processing(d1,k,freq,temps,fcode,code)
#        return indice1,correction1,SNR1r,SNR1i,df1tmp,puissance1,puissance1code,puissance1noise
            indice1_lst.append(indice1+correction1)
            SNR1r_lst.append(SNR1r)
            SNR1i_lst.append(SNR1i)
            df1.append(df1tmp)

            if remote==0:
                d2 = np.array(d[2::4], dtype=complex)
                d2.imag = np.array(d[3::4])
                d2 -= np.mean(d2)
                indice2,correction2,SNR2r,SNR2i,df2tmp,puissance2,puissance2code,puissance2noise=processing(d2,k,freq,temps,fcode,code)
                indice2_lst.append(indice2+correction2)
                SNR2r_lst.append(SNR2r)
                SNR2i_lst.append(SNR2i)
                df2.append(df2tmp)
            if ( (p==1) and (affiche==1)):
                plt.figure()
                plt.plot(abs(prnmap01[indice1-2:indice1+3]))
                if remote==0:
                    plt.plot(abs(prnmap02[indice2-2:indice2+3]))
                    plt.figure()
                    plt.plot(np.real(np.concatenate( (yinti[indice2-1:] , yinti[:indice2-1]) ))[0:1001]/max(np.real(yinti[indice2-2:])))
                    plt.plot(codetmp[0:1001])
                plt.show()
# year month day hour minute second delay frequency power SNR
            if (debug == 1):
                if (remote == 0):
                    print(str(p)+": "+str(indice1)+" "+str(correction1)+" "+str(indice2)+" "+str(correction2))
                else:
                    print(str(p)+": "+str(indice1)+" "+str(correction1))
            if (remote == 0):
                print(str(p)+" "+datetime.utcfromtimestamp(ts+p).strftime('%Y %m %d %H %M %S')+"\t"+str(round((indice1+correction1)/fs/3,12))+"\t"+str(round(df1tmp,3))+"\t"+str(round(10*np.log10(puissance1),1))+"\t"+str(round(10*np.log10(SNR1i+SNR1r),1))+"\t"+str(round((indice2+correction2)/fs/(2*Nint+1),12))+"\t"+str(round(df2tmp,3))+"\t"+str(round(10*np.log10(puissance2),1))+"\t"+str(round(10*np.log10(SNR2i+SNR2r),1)))
            else:
                print(str(p)+" "+datetime.utcfromtimestamp(ts+p).strftime('%Y %m %d %H %M %S')+"\t"+str(round((indice1+correction1)/fs/3,12))+"\t"+str(round(df1tmp,3))+"\t"+str(round(10*np.log10(puissance1),1))+"\t"+str(round(10*np.log10(SNR1i+SNR1r),1)))
            p += 1

ranging("1671606372short.bin","./noiselen2500000_bitlen22_taps03.bin",foffset,0);
