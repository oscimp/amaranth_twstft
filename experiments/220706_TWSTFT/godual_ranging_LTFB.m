pkg load signal

fs=5e6;
Nint=2;

f=fopen('LTFB_prn57bpsk22bits.bin');
code=fread(f,inf,'int8');
code=repelems(code,[[1:length(code)] ; ones(1,length(code))*2]); % interpolate
code=code-mean(code);
fcode=conj(fft(code'));
fclose(f);

filelist=dir('./1657100700.bin');
for filenum=1:length(filelist)
  filelist(filenum).name
  f=fopen(filelist(filenum).name);
  
  p=1;
  do
    d=fread(f,4*fs,'int16');  % 1 second
    longueur=length(d);
    d1=d(1:4:end)+j*d(2:4:end);
    d2=d(3:4:end)+j*d(4:4:end);
    d1=d1-mean(d1);
    d2=d2-mean(d2);
    clear d
  %  x1avant=abs(xcorr(d1,code));x1avant=x1avant(length(code):end);
if (longueur==4*fs)  
    freq=linspace(-fs/2,fs/2,length(d1));
    k=find((freq<6200)&(freq>-6200));
    d22=fftshift(abs(fft(d1.^2))); % 0.1 Hz accuracy
    [~,df(p)]=max(d22(k));df(p)=df(p)+k(1)-1;df(p)=freq(df(p))/2;df(p)
    temps=[0:length(d1)-1]'/fs;
    lo=exp(-j*2*pi*df(p)*temps); % frequency offset
  
    y=d1.*lo;                      % frequency transposition
    prnmap01=fftshift(fft(y).*fcode);      % xcorr
    prnmap01=[zeros(length(y)*(Nint),1) ; prnmap01 ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
    prnmap01=ifft(fftshift(prnmap01));       % back to time
    [~,indice1(p)]=max(abs(prnmap01));
    xval1(p)=prnmap01(indice1(p));
    xval1m1(p)=prnmap01(indice1(p)-1);
    xval1p1(p)=prnmap01(indice1(p)+1);
    [u,v]=polyfit([-1:+1]',abs(prnmap01([indice1(p)-1:indice1(p)+1])),2);
    correction1_1(p)=-u(2)/2/u(1);
    [u,v]=polyfit([-2:+2]',abs(prnmap01([indice1(p)-2:indice1(p)+2])),2);
    correction1_2(p)=-u(2)/2/u(1);
    [u,v]=polyfit([-3:+3]',abs(prnmap01([indice1(p)-3:indice1(p)+3])),2);
    correction1_3(p)=-u(2)/2/u(1);

    prnmap02=fftshift(fft(d2).*fcode);      % xcorr
    prnmap02=[zeros(length(d2)*(Nint),1) ; prnmap02 ; zeros(length(d2)*(Nint),1)]; % interpolation to 3x samp_rate
    prnmap02=ifft(fftshift(prnmap02));       % back to time
    [~,indice2(p)]=max(abs(prnmap02));
    xval2(p)=prnmap02(indice2(p));
    xval2m1(p)=prnmap02(indice2(p)-1);
    xval2p1(p)=prnmap02(indice2(p)+1);
    [u,v]=polyfit([-1:+1]',abs(prnmap02([indice2(p)-1:indice2(p)+1])),2);
    correction2_1(p)=-u(2)/2/u(1);
    [u,v]=polyfit([-2:+2]',abs(prnmap02([indice2(p)-2:indice2(p)+2])),2);
    correction2_2(p)=-u(2)/2/u(1);
    [u,v]=polyfit([-3:+3]',abs(prnmap02([indice2(p)-3:indice2(p)+3])),2);
    correction2_3(p)=-u(2)/2/u(1);

    p=p+1;
end
  until (longueur<4*fs);
%  until (1>0);
  solution1=indice1+correction1_1;
  solution2=indice2+correction2_1;
  subplot(211)
  plot((solution1-solution2)/(2*Nint+1)/fs); % ranging solution
  xlabel('time (s)')
  ylabel('ranging delay (s)')
  [a,b]=polyfit([1:length(solution1)],(solution1-solution2)/(2*Nint+2)/fs,2);
  subplot(212)
  plot((solution1-solution2)/(2*Nint+2)/fs-b.yf); % ranging solution
  std((solution1-solution2)/(2*Nint+2)/fs-b.yf)
  mean((solution1-solution2)/(2*Nint+2)/fs-b.yf)
  legend(num2str(std((solution1-solution2)/(2*Nint+2)/fs-b.yf)))
  xlabel('time (s)')
  ylabel('delay - parabolic fit (s)')
  nom=strrep(filelist(filenum).name,'.bin','.mat');
  eval(['save -mat ',nom,' xv* corr* df indic*']);
  clear xv* corr* df indic*
  fclose(f)
end
