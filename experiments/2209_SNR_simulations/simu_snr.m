clear all
close all

pkg load signal
pkg load communications
B=logspace(-4,3,101);              % 1E-4 to 1E3
Nint=2

if (exist('./simu_snr_hiSNR.mat')==2)
   load simu_snr_hiSNR.mat
end

function [S,Sx,Bx,SNRth,SNRmax,SNRfix,SNRfft]=simulation(signal,B,pos)
%%%%%%%% pseudo random 1e4
  m=1
  for Bval=B
    S(m)=var(signal/Bval/2);       % power=sum x^2

    bruit=randn(1,length(signal)); % *Bval*2;
    bruit=bruit-mean(bruit);
    N=var(bruit);                  % power=sum n^2=1
    SNRth(m)=10*log10(S(m)/N);

    x=signal/Bval/2+bruit;
%  Variable abscissa selected as maximum of xcorr
    xx=xcorr(x,signal);
    [Sx(m),b]=max(abs(xx));        % V^2=power
    Bx(m)=std(xx(b+10:b+floor(length(signal)/10)));  % noise=std(xcorr)
    SNRmax(m)=10*log10(Sx(m)/(Bx(m))*S(m)/sqrt(length(signal)));
 
%  Fixed abscissa selected as known location of xcorr maximum
    Sx50=abs(xx((length(xx)+1)/2)); % fixed position
    Bx50=std(xx((length(xx)+1)/2+10:(length(xx)+1)/2+floor(length(signal)/10)));
    SNRfix(m)=10*log10(Sx50/(Bx50)*S(m)/sqrt(length(signal)));

%  Squared signal FFT
    Sfft=fft(x.^2);      % ^2=power => why square of abs() below ???
    Sf=max(abs(Sfft(pos-10:pos+10)).^2); % square is positive so Sfft has a strong power at index 1 (DC)
    Nf=var(Sfft(pos+10:pos+(length(signal)/20)));  % ??? pquoi var ?
    SNRfft(m)=10*log10(4*Sf/Nf/length(signal));    % ??? pourquoi 4
    m=m+1
  end
end

if (1==0) % no frequency offset
if (exist('SNR4')==0)
  load /home/jmfriedt/sdr/SATRE/gr-satre/taps.txt
  signal=taps(1,:);
  signal=repelems(signal,[[1:length(signal)] ; ones(1,length(signal))*Nint]);
  signal=signal-mean(signal);
  S=var(signal)         % power=sum x^2
  [S4,Sx,Bx,SNR4,SNRx41,SNRx42,SNRfft4]=simulation(signal,B,1);
end
figure
% subplot(311)
semilogx(S4./1,SNR4)
hold on
semilogx(S4./1,SNRx41)
semilogx(S4./1,SNRx42)
semilogx(S4./1,SNRfft4)
xlabel('theoretical SNR (no unit)'); % noise power (a.u.)')
ylabel('SNR (dB)')
legend('var(signal)/var(noise)','cross-correlation @ max','cross-correlation @ center','FFT(squared)','location','northwest')
title('1e4 long code')
ylim([-100 100])
grid
end

if (exist('SNR4')==0)
  load /home/jmfriedt/sdr/SATRE/gr-satre/taps.txt
  signal=taps(1,:);
  signal=repelems(signal,[[1:length(signal)] ; ones(1,length(signal))*Nint*10]);
  signal=signal-mean(signal);
  signal=signal.*sin(2*pi*[0:length(signal)-1]/20);
  S=var(signal)         % power=sum x^2
  [S4,Sx,Bx,SNR4,SNRx41,SNRx42,SNRfft4]=simulation(signal,B,length(signal)/10+1);
end
figure
% subplot(311)
semilogx(S4./1,SNR4)
hold on
semilogx(S4./1,SNRx41+6) % +6 : single sideband vs double sideband
semilogx(S4./1,SNRx42+6)
semilogx(S4./1,SNRfft4+6)
xlabel('theoretical SNR (no unit)'); % noise power (a.u.)')
ylabel('SNR (dB)')
legend('var(signal)/var(noise)','cross-correlation @ max','cross-correlation @ center','FFT(squared)','location','northwest')
title('1e4 long code')
ylim([-100 100]);grid on
%%%%%%%% pseudo random 1e5
  
if (exist('SNR5')==0)
  f=fopen('amaranth_twstft/220706_TWSTFT/OP_prn22bpskcode0.bin')
  codec=fread(f,inf,'int8');
  fclose(f);
  codec=codec(1:1e5)';
  signal=codec;
  signal=repelems(signal,[[1:length(signal)] ; ones(1,length(signal))*Nint*10]);
  signal=signal-mean(signal);
  signal=signal.*sin(2*pi*[0:length(signal)-1]/20);
  S=var(signal)  % puissance=sum x^2
  [S5,Sx,Bx,SNR5,SNRx51,SNRx52,SNRfft5]=simulation(signal,B,length(signal)/10+1);
end
figure
semilogx(S5./1,SNR5)
hold on
semilogx(S5./1,SNRx51+6)
semilogx(S5./1,SNRx52+6)
semilogx(S5./1,SNRfft5+6)
xlabel('theoretical SNR (no unit)'); % noise power (a.u.)')
ylabel('SNR (dB)')
legend('var(signal)/var(noise)','cross-correlation @ max','cross-correlation @ center','FFT(squared)','location','northwest')
title('1e5 long code');ylim([-100 100]);grid on

%%%%%%%% pseudo random 1e6
if (exist('SNR6')==0)
  f=fopen('amaranth_twstft/220706_TWSTFT/OP_prn22bpskcode0.bin')
  codec=fread(f,inf,'int8');
  fclose(f);
  signal=codec(1:1e6)*2;
  signal=repelems(signal,[[1:length(signal)] ; ones(1,length(signal))*Nint*10]);
  signal=signal-mean(signal);
  signal=signal.*sin(2*pi*[0:length(signal)-1]/20);
  S=var(signal)  % puissance=sum x^2
  [S6,Sx,Bx,SNR6,SNRx61,SNRx62,SNRfft6]=simulation(signal,B,length(signal)/10+1);
end
% subplot(313)
figure
semilogx(S6./1,SNR6)
hold on
semilogx(S6./1,SNRx61+6)
semilogx(S6./1,SNRx62+6)
semilogx(S6./1,SNRfft6+6)
xlabel('theoretical SNR (no unit)'); % noise power (a.u.)')
ylabel('SNR (dB)')
legend('var(signal)/var(noise)','cross-correlation @ max','cross-correlation @ center','FFT(squared)','location','northwest')
title('1e6 long code');ylim([-100 100]);grid on
