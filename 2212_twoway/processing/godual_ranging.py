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

def ranging(filename, prn_code):
    print(filename[-14:-4])
    ts = int(filename[-14:-4])

    with open(prn_code, "rb") as fd:
        codeb = fd.read()
        print(codeb[0:20])
        code = list(codeb)
        code=np.repeat(code,2)  # interpolate
        print(code[0:40])
        code=code*2-1
        fcode=np.conj(np.fft.fft(code))
    freq = np.linspace(-fs/2, (fs/2), num=len(code), dtype=float)
    k=np.nonzero((np.array(freq) < 2*(foffset+frange)) & (np.array(freq) > 2*(foffset-frange)))
    k=k[0];
    temps = np.array(range(0, len(code))) / fs
    p = 0
    df = []
    indice1_lst = []
    indice2_lst = []
    SNR1r_lst = []
    SNR1i_lst = []
    SNR2r_lst = []
    SNR2i_lst = []
    interpolation1=np.zeros((Nint*2+1)*len(code))+1j*np.zeros((Nint*2+1)*len(code))  # prepare empty array for interpolation
    interpolation2=np.zeros((Nint*2+1)*len(code))+1j*np.zeros((Nint*2+1)*len(code))
    yint=np.zeros((2*Nint+1)*len(code))+1j*np.zeros((2*Nint+1)*len(code))
    with open(filename, "rb") as fd:
        must_stop = False
        while(not must_stop):
            data = fd.read(len(code) * 4 * 2)
            if len(data) != len(code) * 4 * 2:
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
            dftmp = freq[tmp]/2
            df.append(tmp)
            lo = np.exp(-1j * 2 * np.pi * dftmp * temps)
            y = d1 * lo              # frequency transposition
            fft1tmp=np.fft.fft(y)
            fft2tmp=np.fft.fft(d2)
            multmp1 = fft1tmp * fcode
            multmp2 = fft2tmp * fcode
#            interpolation1=np.concatenate( (np.zeros(len(y))+1j*np.zeros(len(y)) , multmp1, np.zeros(len(y))+1j*np.zeros(len(y))))     # Nint=1
            interpolation1[:len(y)//2]=multmp1[:len(y)//2]
            interpolation1[-len(y)//2:]=multmp1[-len(y)//2:]
#            interpolation2=np.concatenate( (np.zeros(len(d2))+1j*np.zeros(len(d2)) , multmp2, np.zeros(len(d2))+1j*np.zeros(len(d2)))) # Nint=1
            interpolation2[:len(y)//2]=multmp2[:len(y)//2]
            interpolation2[-len(y)//2:]=multmp2[-len(y)//2:]
#            multmp1 = np.fft.fftshift(interpolation1)
#            multmp2 = np.fft.fftshift(interpolation2)
            prnmap01 = np.fft.ifft(interpolation1)       # correlation with returned signal
            prnmap02 = np.fft.ifft(interpolation2)

            indice1 = abs(prnmap01).argmax()      # only one correlation peak
            indice2 = abs(prnmap02).argmax()
            xval1 = prnmap01[indice1]
            xval2 = prnmap02[indice2]
            xval1m1= prnmap01[indice1-1]
            xval1p1 = prnmap01[indice1+1]
            xval2m1 = prnmap02[indice2-1]
            xval2p1 = prnmap02[indice2+1]
            if ( (p==1) and (affiche==1)):
                plt.figure()
                plt.plot(abs(prnmap01[indice1-2:indice1+3]))
                plt.plot(abs(prnmap02[indice2-2:indice2+3]))
                plt.show()
            correction1=((abs(xval1m1)-abs(xval1p1))/(abs(xval1m1)+abs(xval1p1)-2*abs(xval1))/2);
            correction2=((abs(xval2m1)-abs(xval2p1))/(abs(xval2m1)+abs(xval2p1)-2*abs(xval2))/2);
            
  # SNR1 computation
#            yf = np.fft.fftshift(np.fft.fft(y))
#            yint = np.concatenate( (np.zeros(len(y))+1j*np.zeros(len(yf)) , yf , np.zeros(len(y))+1j*np.zeros(len(y))))  # Nint=1
#            yint=np.fft.ifft(np.fft.fftshift(yint))                     # back to time /!\ outer fftshift for 0-delay at center
            yint[:len(y)//2]=fft1tmp[:len(y)//2]
            yint[-len(y)//2:]=fft1tmp[-len(y)//2:]
            yinti=np.fft.ifft(yint) 
            codetmp=np.repeat(code,2*Nint+1)   # interpolate 2*Nint+1
            yincode=np.concatenate((yinti[indice1-2:] , yinti[:indice1-2]))*codetmp; # -2 JMF CHECK WHY -2
            SNR1r=np.mean(np.real(yincode))**2/np.var(yincode);
            SNR1i=np.mean(np.imag(yincode))**2/np.var(yincode);
            puissance1=np.var(y)

  # SNR2 computation
            #yf = np.fft.fftshift(np.fft.fft(d2))
            #yint = np.concatenate( (np.zeros(len(y))+1j*np.zeros(len(yf)) , yf , np.zeros(len(y))+1j*np.zeros(len(y))))  # Nint=1
            #yint=np.fft.ifft(np.fft.fftshift(yint))                     # back to time /!\ outer fftshift for 0-delay at center
            yint[:len(y)//2]=fft2tmp[:len(y)//2]
            yint[-len(y)//2:]=fft2tmp[-len(y)//2:]
            yinti=np.fft.ifft(yint) 
            # if ( (p==fs/len(code)*10) and (affiche==1)):
            if ( (p==1) and (affiche==1)):
                plt.figure()
                plt.plot(np.real(np.concatenate( (yinti[indice2-2:] , yinti[:indice2-2]) ))[0:1001]/max(np.real(yinti[indice2-2:])))
                plt.plot(codetmp[0:1001])
                plt.show()
            yincode=np.concatenate((yinti[indice2:] , yinti[:indice2]))*codetmp; # -2 JMF CHECK WHY -2
            SNR2r=np.mean(np.real(yincode))**2/np.var(yincode);
            SNR2i=np.mean(np.imag(yincode))**2/np.var(yincode);
            puissance2=np.mean(np.real(yincode))**2+np.mean(np.imag(yincode))**2
            indice1_lst.append(indice1+correction1)
            indice2_lst.append(indice2+correction2)
            SNR1r_lst.append(SNR1r)
            SNR1i_lst.append(SNR1i)
            SNR2r_lst.append(SNR2r)
            SNR2i_lst.append(SNR2i)
# year month day hour minute second delay frequency power SNR
            if (debug == 1):
                print(str(p)+": "+str(indice1)+" "+str(correction1)+" "+str(indice2)+" "+str(correction2)+" "+str(round(abs(xval1m1),0))+" "+str(round(abs(xval1),0))+" "+str(round(abs(xval1p1),0))+" "+str(round(abs(xval2m1),0))+" "+str(round(abs(xval2),0))+" "+str(round(abs(xval2p1),0)))
            print(str(p)+": "+datetime.utcfromtimestamp(ts+p).strftime('%Y %m %d %H %M %S')+"\t"+str(round((indice1-indice2+correction1-correction2)/fs/3,12))+"\t"+str(round(dftmp,1))+"\t"+str(round(10*np.log10(puissance1),1))+"\t"+str(round(10*np.log10(SNR1i+SNR1r),1))+"\t"+str(round(10*np.log10(SNR2i+SNR2r),1)))
            p += 1

ranging("../tmp/1670074501.bin","../codes/noiselen500000_bitlen19_taps39.bin");
