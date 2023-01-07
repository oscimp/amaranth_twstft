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
debug=1

if (affiche==1):
    import matplotlib.pyplot as plt

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
    in_array11 = pyfftw.empty_aligned(len(code), dtype=np.complex128)
    out_array11= pyfftw.empty_aligned(len(code), dtype=np.complex128)
    in_array31 = pyfftw.empty_aligned((Nint*2+1)*len(code), dtype=np.complex128)
    out_array31= pyfftw.empty_aligned((Nint*2+1)*len(code), dtype=np.complex128)
    fftw_fobject11 = pyfftw.FFTW(in_array11, out_array11, direction="FFTW_FORWARD", flags=("FFTW_ESTIMATE", ), threads=1)
    fftw_robject31 = pyfftw.FFTW(in_array31, out_array31, direction="FFTW_BACKWARD", flags=("FFTW_ESTIMATE", ), threads=1)
    interpolation1=np.zeros((Nint*2+1)*len(code))+1j*np.zeros((Nint*2+1)*len(code))  # prepare empty array for interpolation
    yint1=np.zeros((2*Nint+1)*len(code))+1j*np.zeros((2*Nint+1)*len(code))
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
            in_array11[:]=d1*d1
            d1_fft=fftw_fobject11(in_array11)
            d1_fft=np.concatenate((d1_fft[int(len(d1_fft)/2):],d1_fft[:int(len(d1_fft)/2)])) # d1_fft = (np.abs(np.fft.fftshift(...)))
            tmp = abs(d1_fft[k]).argmax()+k[0]
            df1tmp = freq[tmp]/2
            lo = np.exp(-1j * 2 * np.pi * df1tmp * temps)
            y1 = d1 * lo                             # frequency transposition
            a=np.polyfit(np.arange(1,fs//3,10)/fs,np.convolve(np.angle(y1[0:int(fs//3):10]),np.ones(100)/100)[49:-50],1)
            dfleftover1=a[0]/2/np.pi
            lo=np.exp(-1j*2*np.pi*dfleftover1*temps) # frequency offset
            y1=y1 * lo                               # fine frequency transposition
            df1tmp+=dfleftover1
            df1.append(df1tmp)
            in_array11[:]=y1
            fft1tmp = fftw_fobject11(in_array11)
            multmp1 = fft1tmp * fcode
#            interpolation1=np.zeros((Nint*2+1)*len(code))+1j*np.zeros((Nint*2+1)*len(code))  # prepare empty array for interpolation
            interpolation1[:len(y1)//2]=multmp1[:len(y1)//2]
            interpolation1[-len(y1)//2:]=multmp1[-len(y1)//2:]
            in_array31[:]=interpolation1               # first interpolated correlation peak
            prnmap01 = fftw_robject31(in_array31)
            indice1 = np.argmax(np.abs(prnmap01))      # only one correlation peak
            xval1 = prnmap01[indice1]
            xval1m1= prnmap01[indice1-1]
            xval1p1 = prnmap01[indice1+1]
            correction1=((abs(xval1m1)-abs(xval1p1))/(abs(xval1m1)+abs(xval1p1)-2*abs(xval1))/2);
            if debug==1:
                print(indice1)
                print(str(df1tmp)+" + "+str(dfleftover1))
                print(xval1m1)
                print(xval1)
                print(xval1p1)
# SNR1 computation
#            yint1=np.zeros((2*Nint+1)*len(code))+1j*np.zeros((2*Nint+1)*len(code))
            yint1[:len(y1)//2]=fft1tmp[:len(y1)//2]
            yint1[-len(y1)//2:]=fft1tmp[-len(y1)//2:]
            in_array31[:]=yint1
            yinti1 = fftw_robject31(in_array31)
            codetmp=np.repeat(code,2*Nint+1)   # interpolate 2*Nint+1
            yincode1=np.concatenate((yinti1[indice1-1:] , yinti1[:indice1-1]))*codetmp;
            SNR1r=np.mean(np.real(yincode1))**2/np.var(yincode1);
            SNR1i=np.mean(np.imag(yincode1))**2/np.var(yincode1);
            puissance1=np.var(y1)
            indice1_lst.append(indice1+correction1)
            SNR1r_lst.append(SNR1r)
            SNR1i_lst.append(SNR1i)

            if remote==0:
                d2 = np.array(d[2::4], dtype=complex)
                d2.imag = np.array(d[3::4])
                d2 -= np.mean(d2)
                in_array11[:]=d2*d2
                d2_fft = fftw_fobject11(in_array11)
                d2_fft =np.concatenate((d2_fft[int(len(d2_fft)/2):],d2_fft[:int(len(d2_fft)/2)])) # d2_fft = np.fft.fftshift(np.abs(np.fft.fft(d2 * d2)))
                tmp = abs(d2_fft[k]).argmax()+k[0]
                df2tmp = freq[tmp]/2
                lo = np.exp(-1j * 2 * np.pi * df2tmp * temps)
                y2 = d2 * lo              # frequency transposition
                a=np.polyfit(np.arange(1,fs//3,10)/fs,np.convolve(np.angle(y2[0:int(fs//3):10]),np.ones(100)/100)[49:-50],1)
                dfleftover2=a[0]/2/np.pi
                lo=np.exp(-1j*2*np.pi*dfleftover2*temps) # frequency offset
                y2=y2 * lo                               # fine frequency transposition
                df2tmp+=dfleftover2;
                df2.append(tmp)
                in_array11[:]=y2
                fft2tmp = fftw_fobject11(in_array11)
                multmp2 = (fft2tmp * fcode)
#            interpolation2=np.zeros((Nint*2+1)*len(code))+1j*np.zeros((Nint*2+1)*len(code))
                interpolation2[:len(y2)//2]=multmp2[:len(y2)//2]
                interpolation2[-len(y2)//2:]=multmp2[-len(y2)//2:]
                in_array31[:]=interpolation2               # second interpolated correlation peak
                prnmap02 = fftw_robject31(in_array31)
                indice2 = abs(prnmap02).argmax()
                xval2 = prnmap02[indice2]
                xval2m1 = prnmap02[indice2-1]
                xval2p1 = prnmap02[indice2+1]
                if debug==1:
                    print(indice2)
                    print(str(df2tmp)+" + "+str(dfleftover2))
                    print(xval2m1)
                    print(xval2)
                    print(xval2p1)
                correction2=((abs(xval2m1)-abs(xval2p1))/(abs(xval2m1)+abs(xval2p1)-2*abs(xval2))/2);
# SNR2 computation
            #yf = np.fft.fftshift(np.fft.fft(d2))
            #yint = np.concatenate( (np.zeros(len(y))+1j*np.zeros(len(yf)) , yf , np.zeros(len(y))+1j*np.zeros(len(y))))  # Nint=1
            #yint=np.fft.ifft(np.fft.fftshift(yint))                     # back to time /!\ outer fftshift for 0-delay at center
                yint2[:len(y2)//2]=fft2tmp[:len(y2)//2]
                yint2[-len(y2)//2:]=fft2tmp[-len(y2)//2:]
                in_array31[:]=yint2
                yinti2 = fftw_robject31(in_array31)
                # if ( (p==fs/len(code)*10) and (affiche==1)):
                yincode2=np.concatenate((yinti2[indice2-1:] , yinti2[:indice2-1]))*codetmp;
                SNR2r=np.mean(np.real(yincode2))**2/np.var(yincode2);
                SNR2i=np.mean(np.imag(yincode2))**2/np.var(yincode2);
                puissance2=np.mean(np.real(yincode2))**2+np.mean(np.imag(yincode2))**2
                indice2_lst.append(indice2+correction2)
                SNR2r_lst.append(SNR2r)
                SNR2i_lst.append(SNR2i)

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
