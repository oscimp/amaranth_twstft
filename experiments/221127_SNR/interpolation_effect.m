close all
clear all
pkg load signal

function [z,s,n]=maxcorr(x,y,N)
  xc=fftshift(fft(x).*conj(fft(y)));           
  n=var(xc);
  s=abs(mean(xc))^2;
  ci=[zeros(1,length(xc)*(N),1) xc zeros(1,length(xc)*(N))];
  z=fftshift(ifft(fftshift(ci)));
end


for interpcode=1:3  % impact of code interpolation
  load /home/jmfriedt/sdr/SATRE/gr-satre/taps.txt
  c=taps(1,:); c=2*c-1;  % +/-1                                 % code
  c=repelems(c,[[1:length(c)] ; ones(1,length(c))*interpcode]); % interpolate
  n=rand(1,length(c));n=n-0.5;                                  % noise
  var(c)/var(n)

  for interpfft=1:3
     printf("factor\t\tSNRxcorr\tSNRth\t\tSNRclaudio\tFourier domain\n");
     for factor=[1e-3 1e-2 1e-1 1 10 100]
        x=n/factor+c;                                           % SNR should be 1
        [zc,sc,nc]=maxcorr(c,x,interpfft);                      % FFT xcorr
        SNRth=var(c)/var(n/factor);                             % theoretical value
        SNRxcorr=max(abs(zc))^2/var(zc(1:length(zc)/2-10))/sqrt(length(c));  % xcorr value
       SNRclaudio=mean(x.*c).^2/var(x.*c);                      % spectrum spreading removal
       printf("%f\t%f\t%f\t%f\t%f\n",factor^2,SNRxcorr,SNRth,SNRclaudio,sc/nc);
     end
   end
end
