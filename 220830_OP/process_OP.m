pkg load signal
graphics_toolkit('gnuplot')

%%%%%%%%%% CONFIGURATION
% SATRE OP
fs=5e6;              % sampling frequency
fc=2.5e6;            % code frequency
foff=-50000-8944;    % frequency offset center
frange=8000          % frequency offset range
Nint=2;              % interpolation factor 2*Nint+1
satre=1;             % satre or Zynq
codeindex=0;         % decoded code index OP
filename="15h30.bin" % filename

% SATRE UME
if(1==0)
fs=5e6;              % sampling frequency
fc=2.5e6;            % code frequency
foff=-50000+35777;   % frequency offset center
frange=8000          % frequency offset range
Nint=1;              % interpolation factor 2*Nint+1
satre=1;             % satre or Zynq
codeindex=19;        % decoded code index National Metrology Institute (UME) of Turkey
filename="15h30.bin" % filename
end

% Zynq
if(1==1)
fs=5e6;              % sampling frequency
fc=2.5e6;            % code frequency
foff=0;              % frequency offset center
frange=8000          % frequency offset range
Nint=1;              % interpolation factor 2*Nint+1
satre=0;             % satre or Zynq
codeindex=0;         % decoded code index
filename="15h30.bin" % filename
end
%%%%%%%%%% END OF CONFIGURATION

codeindex=codeindex+1;   % SATRE code starts at 0, Matlab index at 1
if (satre==1)
  codeduration=10000/fc; % 4 ms
else
  codeduration=1;        % s
end

if (satre==1)
  load ../X310/prn_gene.txt
  code=prn_gene(codeindex,:);
else
  f=fopen('../amaranth_twstft/220706_TWSTFT/OP_prn22bpskcode0.bin');
  code=fread(f,inf,'int8');
  fclose(f);
end
code=repelems(code,[[1:length(code)] ; ones(1,length(code))*fs/fc]); % interpolate
code=code-mean(code);
fcode=conj(fft(code'));

filename
f=fopen(filename);
 
% 15h06 : SATRE 06-15 puis Zynq 08-08+15=23
% 15h30 : SATRE 30-39 puis Zynq 32-32+15=47
% 17h06 : SATRE 06-15 puis Zynq 08-08+15=23
%                 \- 06:24 passe -21 `a -18 dBm TX

% indice=(20)*fs*2*2*2   % fast forward in file to find signals
% fseek(f,indice)        % 2 bytes * 4 channels * complex * fs * 7 min
% 80  s : -114933 -25228       <- -114=-50k-8944+1400 kHz (offset Telstar)
% 420 s : -114933 -25228 2800  <- +1400 Hz offset telstar
% 680 s :         -25228 2800  <- (-50+37.777+1400)*2

% p = 124 ans = 10.750
% p = 125 ans = 3997.3
% p = 126 ans = 1589.3 <- debut de l'emission
% p = 127 ans = 1589.3
% p = 128 ans = 1589.3
% p = 129 ans = 1589.3

p=1;
freq=linspace(-fs/2,fs/2,fs*codeduration);
freqindex=find((freq>2*(foff-frange))&(freq<2*(foff+frange))); % 2* since squared
do
  d=fread(f,4*fs*codeduration,'int16');  % 1 second
  longueur=length(d);
  d1=d(1:4:end)+j*d(2:4:end);
  d1=d1-mean(d1);
  if (satre!=1) 
    d2=d(3:4:end)+j*d(4:4:end);
    d2=d2-mean(d2);
  end
  clear d
  if (longueur==4*fs*codeduration)  
    d22=fftshift(abs(fft(d1.^2)));       % 1 Hz accuracy for SDR
    [valmax_square(p),df(p)]=max(d22(freqindex));tmpdf(p)=df(p)+freqindex(1)-1;df(p)=freq(tmpdf(p))/2;df(p)
%  plot(freq,d22);pause
    noise_square(p)=var(d22(tmpdf(p)+20:tmpdf(p)+10020));
    temps=[0:length(d1)-1]'/fs;
    lo=exp(-j*2*pi*df(p)*temps);         % frequency offset
  
    y=d1.*lo;                            % frequency transposition
    prnmap01=fftshift(fft(y).*fcode);    % xcorr
    prnmap01=[zeros(length(y)*(Nint),1) ; prnmap01 ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
    prnmap01=ifft(fftshift(prnmap01));   % back to time
    [~,indice1(p)]=max(abs(prnmap01));
% plot(abs(prnmap01(indice1(p)-10000:indice1(p)+10000)));pause
    xval1(p)=prnmap01(indice1(p));
    xval1m1(p)=prnmap01(indice1(p)-1);
    xval1p1(p)=prnmap01(indice1(p)+1);
% polyfit on 3 points: same performance than the analytical solution
%      [u,v]=polyfit([-1:+1]',abs(prnmap01([indice1(p)-1:indice1(p)+1])),2);
%      correction1_1(p)=-u(2)/2/u(1);
% fit on 5 or 7 points degrades the result vvvv
%      [u,v]=polyfit([-2:+2]',abs(prnmap01([indice1(p)-2:indice1(p)+2])),2);
%      correction1_2(p)=-u(2)/2/u(1);
%      [u,v]=polyfit([-3:+3]',abs(prnmap01([indice1(p)-3:indice1(p)+3])),2);
%      correction1_3(p)=-u(2)/2/u(1);
    correction1_a(p)=(abs(prnmap01(indice1(p)-1))-abs(prnmap01(indice1(p)+1)))/(abs(prnmap01(indice1(p)-1))+abs(prnmap01(indice1(p)+1))-2*abs(prnmap01(indice1(p))))/2;
    if ((indice1(p)+1020)<length(prnmap01))
      bruit1(p)=var(prnmap01(indice1(p)+20:indice1(p)+1020));
    end
 
    if (satre!=1) 
      prnmap02=fftshift(fft(d2).*fcode);             % xcorr
      prnmap02=[zeros(length(d2)*(Nint),1) ; prnmap02 ; zeros(length(d2)*(Nint),1)]; % interpolation to 3x samp_rate
      prnmap02=ifft(fftshift(prnmap02));       % back to time
      [~,indice2(p)]=max(abs(prnmap02));
      xval2(p)=prnmap02(indice2(p));
      xval2m1(p)=prnmap02(indice2(p)-1);
      xval2p1(p)=prnmap02(indice2(p)+1);
%        [u,v]=polyfit([-1:+1]',abs(prnmap02([indice2(p)-1:indice2(p)+1])),2);
%        correction2_1(p)=-u(2)/2/u(1);
%        [u,v]=polyfit([-2:+2]',abs(prnmap02([indice2(p)-2:indice2(p)+2])),2);
%        correction2_2(p)=-u(2)/2/u(1);
%        [u,v]=polyfit([-3:+3]',abs(prnmap02([indice2(p)-3:indice2(p)+3])),2);
%        correction2_3(p)=-u(2)/2/u(1);
      correction2_a(p)=(abs(prnmap02(indice2(p)-1))-abs(prnmap02(indice2(p)+1)))/(abs(prnmap02(indice2(p)-1))+abs(prnmap02(indice2(p)+1))-2*abs(prnmap02(indice2(p))))/2;
      bruit2(p)=var(prnmap02(indice2(p)+20:indice2(p)+10020));
    end
    p=p+1
  end
until (longueur<4*fs*codeduration);
%  until (p>600);

solution1=indice1+correction1_a;
if (satre!=1) solution2=indice2+correction2_a;end
subplot(211)
if (satre!=1)
  plot((solution1-solution2)/(2*Nint+1)/fs); % ranging solution
else
  plot((solution1)/(2*Nint+1)/fs);           % ranging solution
end
xlabel('time (s)')
ylabel('ranging delay (s)')
if (satre!=1)
   [a,b]=polyfit([1:length(solution1)],(solution1-solution2)/(2*Nint+1)/fs,2);
else
   [a,b]=polyfit([1:length(solution1)],(solution1)/(2*Nint+1)/fs,2);
end
subplot(212)
if (satre!=1)
  plot((solution1-solution2)/(2*Nint+1)/fs-b.yf); % ranging solution
  std((solution1-solution2)/(2*Nint+1)/fs-b.yf)
  mean((solution1-solution2)/(2*Nint+1)/fs-b.yf)
  legend(num2str(std((solution1-solution2)/(2*Nint+1)/fs-b.yf)))
else
  plot((solution1)/(2*Nint+1)/fs-b.yf); % ranging solution
  std((solution1)/(2*Nint+1)/fs-b.yf)
  mean((solution1)/(2*Nint+1)/fs-b.yf)
  legend(num2str(std((solution1)/(2*Nint+1)/fs-b.yf)))
end
xlabel('time (s)')
ylabel('delay - parabolic fit (s)')
% nom=strrep(filename,'.bin','.mat');
% eval(['save -mat ',nom,' xv* corr* df indic*']);
% clear xv* corr* df indic*
fclose(f)
