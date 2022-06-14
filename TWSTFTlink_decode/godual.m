pkg load signal

fs=5e6;
f=fopen('prn22bpskcode0.bin');
code=fread(f,inf,'int8');
code=repelems(code,[[1:length(code)] ; ones(1,length(code))*2]); % interpolate
code=code-mean(code);
fcode=conj(fft(code'));
fclose(f);

filelist=dir('./*B210*dual.bin');
for filenum=1:length(filelist)
  filelist(filenum).name
  f=fopen(filelist(filenum).name);
  d=fread(f,20*fs,'int16'); % remove header before starting emission
  
  p=1;
  do
    d=fread(f,4*fs,'int16');  % 2 second
    longueur=length(d);
    d1=d(1:4:end)+j*d(2:4:end);
    d2=d(3:4:end)+j*d(4:4:end);
    d1=d1-mean(d1);
    d2=d2-mean(d2);
    clear d
  %  x1avant=abs(xcorr(d1,code));x1avant=x1avant(length(code):end);
if (longueur==4*fs)  
    freq=linspace(-fs/2,fs/2,length(d1));
    k=find((freq<5000)&(freq>50));
    d22=fftshift(abs(fft(d1.^2))); % 0.1 Hz accuracy
    [~,df(p)]=max(d22(k));df(p)=df(p)+k(1)-1;df(p)=freq(df(p))/2
    temps=[0:length(d1)-1]'/fs;
    lo=exp(-j*2*pi*df(p)*temps); % frequency offset
  
    y=d1.*lo;                      % frequency transposition
    prnmap01=ifft(fft(y).*fcode);  % correlation with returned signal
    prnmap02=ifft(fft(d2).*fcode); % correlation with reference signal
    [~,indice1(p)]=max(abs(prnmap01)); % only one correlation peak
    [~,indice2(p)]=max(abs(prnmap02)); % only one correlation peak
    xval1(p)=prnmap01(indice1(p));
    xval2(p)=prnmap02(indice2(p));
    xval1m1(p)=prnmap01(indice1(p)-1);
    xval1p1(p)=prnmap01(indice1(p)+1);
    xval2m1(p)=prnmap02(indice2(p)-1);
    xval2p1(p)=prnmap02(indice2(p)+1);
    [u,v]=polyfit([-1:+1]',abs(prnmap01([indice1(p)-1:indice1(p)+1])),2);
    correction1(p)=-u(2)/2/u(1);
    [u,v]=polyfit([-1:+1]',abs(prnmap02([indice2(p)-1:indice2(p)+1])),2);
    correction2(p)=-u(2)/2/u(1);
    p=p+1;
end
  until (longueur<4*fs);
  solution1=indice1+correction1;
  solution2=indice2+correction2;
  plot((solution1-solution2)/fs); % ranging solution
  nom=strrep(filelist(filenum).name,'.bin','.mat');
  eval(['save -mat ',nom,' xv* corr* df indic*']);
  clear xv* corr* df indic*
  fclose(f)
end
