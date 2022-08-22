pkg load signal

fs=5e6;    % sampling rate
fd=2.5e6;  % chiprate
f=fopen('../prn3bpsk22bits.bin');
codec=fread(f,inf,'int8');
fclose(f);
N=fs/fd;   % interpolation
D=1;       % decimation
codec=codec-mean(codec);
codec=repelems(codec,[[1:length(codec)] ; ones(1,length(codec))*N]); % interpolate
codec=codec(1:D:end); 
fcode=conj(fft(codec.'));

filenum=1;
filelist=dir('bpsk_data.bin');
for filenum=1:length(filelist)
  f=fopen([filelist(filenum).name]);
  p=1;
  do
    d=fread(f,2*fs,'int16');  % 1 second
    longueur=length(d);
    if (longueur==2*fs)  
      d1=d(1:2:end)+j*d(2:2:end);
      clear d
      d1=d1-mean(d1);
      freq=linspace(-fs/2,fs/2,length(d1));
      
      k=find((freq<5000)&(freq>-5000));
      d22=fftshift(abs(fft(d1.^2))); % 0.1 Hz accuracy
      [~,df]=max(d22(k));df=df+k(1)-1;df=freq(df)/2;
      temps=[0:length(d1)-1]'/fs;
      lo=exp(-j*2*pi*df*temps); % frequency offset
      y=d1.*lo;                      % frequency transposition
      
      prnmap01=ifft(fft(y).*fcode);  % correlation with returned signal
      [valmax,indice1(p)]=max(abs(prnmap01)); % only one correlation peak
      xval1(p)=prnmap01(indice1(p));
      xval1m1(p)=prnmap01(indice1(p)-1);
      xval1p1(p)=prnmap01(indice1(p)+1);
      [u,v]=polyfit([-1:+1]',abs(prnmap01([indice1(p)-1:indice1(p)+1])),2);
      correction1(p)=-u(2)/2/u(1);
      p=p+1;
%      figure;plot(abs(prnmap01));
    end
  until (longueur<2*fs);
solution1=indice1+correction1;
subplot(211)
plot((solution1-mean(solution1))/fs); % ranging solution
std(solution1/fs)
legend('BPSK')
xlabel('time (s)'); ylabel('delay (s)')
nom=strrep(filelist(filenum).name,'.bin','.mat');
%  eval(['save -mat ',nom,' xv* corr* df indic*']);
%  clear xv* corr* df indic*
end
