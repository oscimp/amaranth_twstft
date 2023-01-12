#!/usr/bin/env python3

import numpy as np
import struct
import array
import pyfftw  # from https://blog.hpc.qmul.ac.uk/pyfftw.html
from datetime import datetime

fs = (5e6)
foffset=0
frange=8000
Nint=1
affiche=0
debug=0

if (affiche==1):
    import matplotlib.pyplot as plt

def processing(d,k,freq,temps,fcode,code):
    in_array11 = pyfftw.empty_aligned(len(code), dtype=np.complex128)
    out_array11= pyfftw.empty_aligned(len(code), dtype=np.complex128)
    in_array31 = pyfftw.empty_aligned((Nint*2+1)*len(code), dtype=np.complex128)
    out_array31= pyfftw.empty_aligned((Nint*2+1)*len(code), dtype=np.complex128)
    fftw_fobject11 = pyfftw.FFTW(in_array11, out_array11, direction="FFTW_FORWARD", flags=("FFTW_ESTIMATE", ), threads=1)
    fftw_robject31 = pyfftw.FFTW(in_array31, out_array31, direction="FFTW_BACKWARD", flags=("FFTW_ESTIMATE", ), threads=1)
    interpolation=np.zeros((Nint*2+1)*len(code))+1j*np.zeros((Nint*2+1)*len(code))  # prepare empty array for interpolation
    yint=np.zeros((2*Nint+1)*len(code))+1j*np.zeros((2*Nint+1)*len(code))
    in_array11[:]=d*d
    d_fft=fftw_fobject11(in_array11)
    d_fft=np.concatenate((d_fft[int(len(d_fft)/2):],d_fft[:int(len(d_fft)/2)])) # d1_fft = (np.abs(np.fft.fftshift(...)))
    tmp = abs(d_fft[k]).argmax()+k[0]
    dftmp = freq[tmp]/2
    lo = np.exp(-1j * 2 * np.pi * dftmp * temps)
    y = d * lo                             # frequency transposition
    a=np.polyfit(np.arange(1,fs//3,10)/fs,np.convolve(np.angle(y[0:int(fs//3):10]),np.ones(100)/100)[49:-50],1)
    dfleftover=a[0]/2/np.pi
    lo=np.exp(-1j*2*np.pi*dfleftover*temps) # frequency offset
    y=y * lo                                 # fine frequency transposition
    dftmp+=dfleftover
    in_array11[:]=y
    ffttmp = fftw_fobject11(in_array11)
    multmp = ffttmp * fcode
#   interpolation=np.zeros((Nint*2+1)*len(code))+1j*np.zeros((Nint*2+1)*len(code))  # prepare empty array for interpolation
    interpolation[:len(y)//2]=multmp[:len(y)//2]
    interpolation[-len(y)//2:]=multmp[-len(y)//2:]
    in_array31[:]=interpolation               # first interpolated correlation peak
    prnmap = fftw_robject31(in_array31)
    indice = np.argmax(np.abs(prnmap))        # only one correlation peak
    xval = prnmap[indice]
    xvalm1= prnmap[indice-1]
    xvalp1 = prnmap[indice+1]
    correction=(abs(xvalm1)-abs(xvalp1))/(abs(xvalm1)+abs(xvalp1)-2*abs(xval))/2;
    if debug==1:
        print(indice)
        print(str(dftmp)+" + "+str(dfleftover))
        print(xvalm1)
        print(xval)
        print(xvalp1)
# SNR1 computation
#   yint1=np.zeros((2*Nint+1)*len(code))+1j*np.zeros((2*Nint+1)*len(code))
    yint[:len(y)//2]=ffttmp[:len(y)//2]
    yint[-len(y)//2:]=ffttmp[-len(y)//2:]
    in_array31[:]=yint
    yinti = fftw_robject31(in_array31)
    codetmp=np.repeat(code,2*Nint+1)   # interpolate 2*Nint+1
    yincode=np.concatenate((yinti[indice-1:] , yinti[:indice-1]))*codetmp;
    SNRr=np.mean(np.real(yincode))**2/np.var(yincode);
    SNRi=np.mean(np.imag(yincode))**2/np.var(yincode);
    puissance=np.var(y)
    puissancecode=np.mean(np.real(yincode))**2+np.mean(np.imag(yincode))**2
    puissancenoise=np.var(yincode)
    return indice,correction,SNRr,SNRi,dftmp,puissance,puissancecode,puissancenoise

def ranging(filename, prn_code,foffset,remote):
    print(filename[0:10])
    ts = int(filename[0:10])

    with open(prn_code, "rb") as fd:
        codeb = fd.read()
        print(codeb[0:20])
        code = list(codeb)
        code=np.repeat(code,2)  # interpolate (ASSUMES 2.5 Mchips/2)
        print(code[0:40])
        code=code*2-1
        in_array_code = pyfftw.empty_aligned(len(code), dtype=np.complex128)
        out_array_code= pyfftw.empty_aligned(len(code), dtype=np.complex128)
        fftw_fobject_code = pyfftw.FFTW(in_array_code, out_array_code, direction="FFTW_FORWARD", flags=("FFTW_ESTIMATE", ), threads=1)
        in_array_code[:].real=code
        fcode = np.conj(fftw_fobject_code(in_array_code))
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
        yint2=np.zeros((2*Nint+1)*len(code))+1j*np.zeros((2*Nint+1)*len(code))
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
            indice1_lst.append(indice1+correction1)
            SNR1r_lst.append(SNR1r)
            SNR1i_lst.append(SNR1i)
            df1.append(df1tmp)

            if remote==0:
                d2 = np.array(d[2::4], dtype=complex)
                d2.imag = np.array(d[3::4])
                d2 -= np.mean(d2)
                indice2,correction2,SNR2r,SNR2i,df2tmp,puissance2,puissance2code,puissance2noise=processing(d2,k,freq,temps,fcode,code)
                indice2_lst.append(indice1+correction1)
                SNR2r_lst.append(SNR2r)
                SNR2i_lst.append(SNR2i)
                df2.append(df2tmp)

            if ( (p==1) and (affiche==1)):
                plt.figure()
                plt.plot(abs(prnmap01[indice1-2:indice1+3]))
                if remote==0:
                    plt.plot(abs(prnmap02[indice2-2:indice2+3]))
                    plt.figure()
                    plt.plot(np.real(np.concatenate( (yinti2[indice2-1:] , yinti2[:indice2-1]) ))[0:1001]/max(np.real(yinti2[indice2-2:])))
                    plt.plot(codetmp[0:1001])
                plt.show()
# year month day hour minute second delay frequency power SNR
            if (debug == 1):
                if (remote == 0):
                    print(str(p)+": "+str(indice1)+" "+str(correction1)+" "+str(indice2)+" "+str(correction2)+" "+str(round(abs(xval1m1),0))+" "+str(round(abs(xval1),0))+" "+str(round(abs(xval1p1),0))+" "+str(round(abs(xval2m1),0))+" "+str(round(abs(xval2),0))+" "+str(round(abs(xval2p1),0)))
                else:
                    print(str(p)+": "+str(indice1)+" "+str(correction1)+" "+str(round(abs(xval1m1),0))+" "+str(round(abs(xval1),0))+" "+str(round(abs(xval1p1),0)))
            if (remote == 0):
                print(str(p)+" "+datetime.utcfromtimestamp(ts+p).strftime('%Y %m %d %H %M %S')+"\t"+str(round((indice1+correction1)/fs/3,12))+"\t"+str(round(df1tmp,3))+"\t"+str(round(10*np.log10(puissance1),1))+"\t"+str(round(10*np.log10(SNR1i+SNR1r),1))+"\t"+str(round((indice2+correction2)/fs/(2*Nint+1),12))+"\t"+str(round(df2tmp,3))+"\t"+str(round(10*np.log10(puissance2),1))+"\t"+str(round(10*np.log10(SNR2i+SNR2r),1)))
            else:
                print(str(p)+" "+datetime.utcfromtimestamp(ts+p).strftime('%Y %m %d %H %M %S')+"\t"+str(round((indice1+correction1)/fs/3,12))+"\t"+str(round(df1tmp,3))+"\t"+str(round(10*np.log10(puissance1),1))+"\t"+str(round(10*np.log10(SNR1i+SNR1r),1)))
            p += 1

ranging("1671606372short.bin","./noiselen2500000_bitlen22_taps03.bin",foffset,0);
