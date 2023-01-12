% https://insidegnss.com/wp-content/uploads/2018/01/novdec10-Solutions.pdf
% BW is the bandwidth of observation, which is usually the noise equivalent bandwidth of the 
% last filter stage in a receiver’s RF front-end.
% Typical values in an L1 C/A code receiver are as follows: C/N0 : ~37 to 45 dB-Hz
% Receiver front-end bandwidth: ~4MHz => BW = 10*log (4,000,000)= 66dB
% SNR = C/N0 – BW => SNR ~ (37 – 66) to (45 – 66) => SNR ~ -29dB to -21dB
% => SATRE : observed C/N0=53 dB - 66 BW => SNR ~ -13 dB
clear all
close all

pkg load signal
pkg load communications
% B=logspace(0,5,101)  % low SNR
B=logspace(-2,1,101); % 101
Nintsig=1
Nintcor=0

function [S,Sx,Bx,SNRth,SNRmax,pos,SNRfft,SNRxx,SNRclaudio]=simulation(signal,B,posf,Nintcor)
%%%%%%%% pseudo random 1e4
  m=1
  for Bval=B
    bruit=randn(1,length(signal)); % *Bval*2;
    bruit=bruit-mean(bruit);
    S(m)=var(signal/Bval);         % power=sum x^2 => keep noise cst and lower signal (signal/Bval)
    N=var(bruit);                  % power=sum n^2=1
    SNRth(m)=10*log10(S(m)/N);

    x=signal/Bval+bruit;           % attenuated signal = observation
%  Variable abscissa selected as maximum of xcorr(x,signal);
    xx=fftshift(fft(x).*conj(fft(signal))); 
    xi=[zeros(length(xx)*(Nintcor),1) ; xx.' ; zeros(length(xx)*(Nintcor),1)]; % interpolation to Nintcor samp_rate
    xx=(ifft(fftshift(xi)));   % /!\ inner fftshift to have 0 frequency on the side, and NO outer for 0-delay at center -> keep 0 at left (index 1)
    [Sx(m),pos(m)]=max(abs(xx));        % V^2=power
    if (pos(m)>length(xx)/2)
       Bx(m)=std(xx(10:pos(m)-10));
    else
       Bx(m)=std(xx(pos(m)+10:end-10));
    end
    SNRmax(m)=10*log10(Sx(m)/Bx(m)/2/sqrt(length(signal))); % *S(m)); <- not known experimentally !
%                                         ^^^ SNR gain from pulse compression ratio by code length

%  Autocorrelation
    xx=fftshift(fft(x).*conj(fft(x))); 
    xi=[zeros(length(xx)*(Nintcor),1) ; xx.' ; zeros(length(xx)*(Nintcor),1)]; % interpolation to Nintcor samp_rate
    xx=(ifft(fftshift(xi)));   % /!\ inner fftshift to have 0 frequency on the side, and NO outer for 0-delay at center -> keep 0 at index 1
    [Sxx(m),posx]=max(abs(xx));       % V^2=power
    if (posx>length(xx)/2)
       Bxx=std(xx(10:pos(m)-10));
    else
       Bxx=std(xx(pos(m)+10:end-10));
    end
    SNRxx(m)=10*log10(Sxx(m)/Bxx/2/sqrt(length(signal))); % *S(m)); <- not known experimentally !
%                                  ^^^ SNR gain from pulse compression ratio by code length
 
%  Squared signal FFT
    Sfft=fft(x.^2);      % ^2=power => why square of abs() below ???
%    Sfft=pwelch(x.^2,[],[],length(x));      % ^2=power => why square of abs() below ???
    if (posf>10)
       Sf=max(abs(Sfft(posf-10:posf+10)).^2); % square is positive so Sfft has a strong power at index 1 (DC)
    else
       Sf=max(abs(Sfft).^2); % square is positive so Sfft has a strong power at index 1 (DC)
    end
    Nf=var(Sfft(posf+10:posf+(length(signal)/20)));  % ??? pquoi var ?
    SNRfft(m)=10*log10(4*Sf/Nf/length(signal));      % ??? pourquoi 4

    SNRclaudio(m)=10*log10(mean(x.*signal)^2/var(x.*signal));
    m=m+1
  end
end

load /home/jmfriedt/sdr/SATRE/gr-satre/taps.txt
signal=taps(1,:);
signal=repelems(signal,[[1:length(signal)] ; ones(1,length(signal))*Nintsig]);
signal=signal-mean(signal);
S=var(signal)         % power=sum x^2
[S4,Sx,Bx,SNR4,SNRx41,pos4,SNRfft4,SNRxx4,SNRclaudio4]=simulation(signal,B,1,Nintcor);

figure
semilogx(S4./1,SNR4)
hold on
semilogx(S4./1,2*SNRx41+6)
semilogx(S4./1,SNRfft4)
semilogx(S4./1,SNRclaudio4)
xlabel('theoretical SNR (no unit)'); % noise power (a.u.)')
ylabel('SNR (dB)')
legend('var(signal)/var(noise)','cross-correlation @ max','FFT(squared)','Claudio','location','northwest')
title('1e4 long code no frequency offset')
ylim([-40 40])
grid

% add frequency offset
signal=signal.*sin(2*pi*[0:length(signal)-1]/20);
S=var(signal)         % power=sum x^2
[S4,Sx,Bx,SNR4,SNRx41,SNRx42,SNRfft4]=simulation(signal,B,length(signal)/10+1,1);
figure
semilogx(S4./1,SNR4)
hold on
semilogx(S4./1,SNRx41*2+6) % +6 : single sideband vs double sideband
semilogx(S4./1,SNRfft4+6) % +6 : single sideband vs double sideband
xlabel('theoretical SNR (no unit)'); % noise power (a.u.)')
ylabel('SNR (dB)')
legend('var(signal)/var(noise)','cross-correlation @ max','FFT(squared)','location','northwest')
title('1e4 long code with frequency offset')
grid on
ylim([-40 40])

