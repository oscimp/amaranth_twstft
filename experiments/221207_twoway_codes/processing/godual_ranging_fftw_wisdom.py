#!/usr/bin/env python3

import numpy as np
import struct
import array
import pyfftw  # from https://blog.hpc.qmul.ac.uk/pyfftw.html
import pickle
from datetime import datetime

fs = (5e6)
foffset=0
frange=8000
Nint=1
affiche=0

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
        in_array_code = pyfftw.empty_aligned(len(code), dtype=np.complex64)
        out_array_code= pyfftw.empty_aligned(len(code), dtype=np.complex64)
        fftw_fobject_code = pyfftw.FFTW(in_array_code, out_array_code, direction="FFTW_FORWARD", flags=("FFTW_ESTIMATE", ), threads=1)
        in_array_code[:].real=code
        fcode = np.conj(fftw_fobject_code(in_array_code))
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
    in_array11 = pyfftw.empty_aligned(len(code), dtype=np.complex64)
    in_array12 = pyfftw.empty_aligned(len(code), dtype=np.complex64)
    in_array13 = pyfftw.empty_aligned(len(code), dtype=np.complex64)
    out_array11= pyfftw.empty_aligned(len(code), dtype=np.complex64)
    out_array12= pyfftw.empty_aligned(len(code), dtype=np.complex64)
    out_array13= pyfftw.empty_aligned(len(code), dtype=np.complex64)
    in_array31 = pyfftw.empty_aligned((Nint*2+1)*len(code), dtype=np.complex64)
    in_array32 = pyfftw.empty_aligned((Nint*2+1)*len(code), dtype=np.complex64)
    in_array33 = pyfftw.empty_aligned((Nint*2+1)*len(code), dtype=np.complex64)
    in_array34 = pyfftw.empty_aligned((Nint*2+1)*len(code), dtype=np.complex64)
    out_array31= pyfftw.empty_aligned((Nint*2+1)*len(code), dtype=np.complex64)
    out_array32= pyfftw.empty_aligned((Nint*2+1)*len(code), dtype=np.complex64)
    out_array33= pyfftw.empty_aligned((Nint*2+1)*len(code), dtype=np.complex64)
    out_array34= pyfftw.empty_aligned((Nint*2+1)*len(code), dtype=np.complex64)
    try: # Try to load FFTW wisdom but don't panic if we can't
        with open("fft.wisdom", "rb") as the_file:
            wisdom = pickle.load(the_file)
            pyfftw.import_wisdom(wisdom)
            print("Wisdom imported")
    except FileNotFoundError:
        print("Warning: wisdom could not be imported")

    try:  # Try to plan our transforms with the wisdom we have already
        fftw_fobject11 = pyfftw.FFTW(in_array11, out_array11, direction="FFTW_FORWARD", flags=("FFTW_WISDOM_ONLY", ), threads=1)
        fftw_fobject12 = pyfftw.FFTW(in_array12, out_array12, direction="FFTW_FORWARD", flags=("FFTW_WISDOM_ONLY", ), threads=1)
        fftw_fobject13 = pyfftw.FFTW(in_array13, out_array13, direction="FFTW_FORWARD", flags=("FFTW_WISDOM_ONLY", ), threads=1)
        fftw_robject31 = pyfftw.FFTW(in_array31, out_array31, direction="FFTW_BACKWARD", flags=("FFTW_WISDOM_ONLY", ), threads=1)
        fftw_robject32 = pyfftw.FFTW(in_array32, out_array32, direction="FFTW_BACKWARD", flags=("FFTW_WISDOM_ONLY", ), threads=1)
        fftw_robject33 = pyfftw.FFTW(in_array33, out_array33, direction="FFTW_BACKWARD", flags=("FFTW_WISDOM_ONLY", ), threads=1)
        fftw_robject34 = pyfftw.FFTW(in_array34, out_array34, direction="FFTW_BACKWARD", flags=("FFTW_WISDOM_ONLY", ), threads=1)

    except RuntimeError as e: # If we don't have enough wisdom, print a warning and proceed. => 16'30" computation time
        print(e)  # will take some time on the first run but save time during subsequent executions
        fftw_fobject11 = pyfftw.FFTW(in_array11, out_array11, direction="FFTW_FORWARD", flags=("FFTW_MEASURE",), threads=1)
        fftw_fobject12 = pyfftw.FFTW(in_array12, out_array12, direction="FFTW_FORWARD", flags=("FFTW_WISDOM_ONLY", ), threads=1)
        fftw_fobject13 = pyfftw.FFTW(in_array13, out_array13, direction="FFTW_FORWARD", flags=("FFTW_WISDOM_ONLY", ), threads=1)
        fftw_robject31 = pyfftw.FFTW(in_array31, out_array31, direction="FFTW_BACKWARD", flags=("FFTW_MEASURE", ), threads=1)
        fftw_robject32 = pyfftw.FFTW(in_array32, out_array32, direction="FFTW_BACKWARD", flags=("FFTW_WISDOM_ONLY", ), threads=1)
        fftw_robject33 = pyfftw.FFTW(in_array33, out_array33, direction="FFTW_BACKWARD", flags=("FFTW_WISDOM_ONLY", ), threads=1)
        fftw_robject34 = pyfftw.FFTW(in_array34, out_array34, direction="FFTW_BACKWARD", flags=("FFTW_WISDOM_ONLY", ), threads=1)

    # Save the wisdom for next time
    with open("fft.wisdom", "wb") as the_file:
        wisdom = pyfftw.export_wisdom()
        pickle.dump(wisdom, the_file)

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

            in_array11[:]=d1*d1
            d1_fft = (np.abs(np.fft.fftshift(fftw_fobject11(in_array11)))) 
            tmp = d1_fft[k].argmax()+k[0]
            dftmp = freq[tmp]/2
            df.append(tmp)
            lo = np.exp(-1j * 2 * np.pi * dftmp * temps)
            y = d1 * lo              # frequency transposition
            in_array12[:]=y
            fft1tmp = fftw_fobject12(in_array12)
            in_array13[:]=d2
            fft2tmp = fftw_fobject13(in_array13)
            multmp1 = (fft1tmp * fcode)
            multmp2 = (fft2tmp * fcode)
            interpolation1=np.zeros((Nint*2+1)*len(code))+1j*np.zeros((Nint*2+1)*len(code))  # prepare empty array for interpolation
            interpolation2=np.zeros((Nint*2+1)*len(code))+1j*np.zeros((Nint*2+1)*len(code))
            interpolation1[:len(y)//2]=multmp1[:len(y)//2]
            interpolation1[-len(y)//2:]=multmp1[-len(y)//2:]
            interpolation2[:len(y)//2]=multmp2[:len(y)//2]
            interpolation2[-len(y)//2:]=multmp2[-len(y)//2:]
            in_array31[:]=interpolation1
            prnmap01 = fftw_robject31(in_array31)
            in_array32[:]=interpolation2
            prnmap02 = fftw_robject32(in_array32)

            indice1 = np.abs(prnmap01).argmax()      # only one correlation peak
            indice2 = np.abs(prnmap02).argmax()
            xval1 = prnmap01[indice1]
            xval2 = prnmap02[indice2]
            xval1m1= prnmap01[indice1-1]
            xval1p1 = prnmap01[indice1+1]
            xval2m1 = prnmap02[indice2-1]
            xval2p1 = prnmap02[indice2+1]

            correction1=((np.abs(xval1m1)-np.abs(xval1p1))/(np.abs(xval1m1)+np.abs(xval1p1)-2*np.abs(xval1))/2);
            correction2=((np.abs(xval2m1)-np.abs(xval2p1))/(np.abs(xval2m1)+np.abs(xval2p1)-2*np.abs(xval2))/2);
            
  # SNR1 computation
            yint1=np.zeros((2*Nint+1)*len(code))+1j*np.zeros((2*Nint+1)*len(code))
            yint1[:len(y)//2]=fft1tmp[:len(y)//2]
            yint1[-len(y)//2:]=fft1tmp[-len(y)//2:]
            in_array33[:]=yint1
            yinti1 = fftw_robject33(in_array33)
            codetmp=np.repeat(code,2*Nint+1)   # interpolate 2*Nint+1
            yincode1=np.concatenate((yinti1[indice1-2:] , yinti1[:indice1-2]))*codetmp; # -2 JMF CHECK WHY -2
            SNR1r=np.mean(np.real(yincode1))**2/np.var(yincode1);
            SNR1i=np.mean(np.imag(yincode1))**2/np.var(yincode1);
            puissance1=np.var(y)

  # SNR2 computation
            yint2=np.zeros((2*Nint+1)*len(code))+1j*np.zeros((2*Nint+1)*len(code))
            yint2[:len(y)//2]=fft2tmp[:len(y)//2]
            yint2[-len(y)//2:]=fft2tmp[-len(y)//2:]
            in_array34[:]=yint2
            yinti2 = fftw_robject34(in_array34)
            # if ( (p==fs/len(code)*10) and (affiche==1)):
            if ( (p==1) and (affiche==1)):
                plt.plot(np.real(np.concatenate( (yinti2[indice2-2:] , yinti2[:indice2-2]) ))[0:1001]/max(np.real(yinti2[indice2-2:])))
                plt.plot(codetmp[0:1001])
                plt.show()
            yincode2=np.concatenate((yinti2[indice2-1:] , yinti2[:indice2-1]))*codetmp; # -2 JMF CHECK WHY -2
            SNR2r=np.mean(np.real(yincode2))**2/np.var(yincode2);
            SNR2i=np.mean(np.imag(yincode2))**2/np.var(yincode2);
            puissance2=np.mean(np.real(yincode2))**2+np.mean(np.imag(yincode2))**2
            indice1_lst.append(indice1+correction1)
            indice2_lst.append(indice2+correction2)
            SNR1r_lst.append(SNR1r)
            SNR1i_lst.append(SNR1i)
            SNR2r_lst.append(SNR2r)
            SNR2i_lst.append(SNR2i)
# year month day hour minute second delay frequency power SNR
            print(str(p)+": "+str(indice1)+" "+str(indice2))
            print(str(p)+": "+datetime.utcfromtimestamp(ts+p).strftime('%Y %m %d %H %M %S')+"\t"+str(round((indice1-indice2+correction1-correction2)/fs/3,12))+"\t"+str(round(dftmp,1))+"\t"+str(round(10*np.log10(puissance1),1))+"\t"+str(round(10*np.log10(SNR1i+SNR1r),1))+"\t"+str(round(10*np.log10(SNR2i+SNR2r),1)))
            p += 1

ranging("../tmp/1670074501.bin","../codes/noiselen500000_bitlen19_taps39.bin");






