pkg load signal
graphics_toolkit('qt')

fs=5e6;

f=fopen('prn22bpskcode0.bin');
code=fread(f,inf,'int8');
code=repelems(code,[[1:length(code)] ; ones(1,length(code))*2]); % interpolate
code=code-mean(code);
fcode=conj(fft(code'));
fclose(f);

filelist=dir('./X310*.bin');
for filenum=1:length(filelist)
  f=fopen(filelist(filenum).name);
  for tmp=1:6
     d=fread(f,20*fs,'int16');   % remove header before starting emission
  end  
  p=1;
  do
    d=fread(f,4*fs,'int16');     % 1 second
    longueur=length(d);
    d1=d(1:4:end)+j*d(2:4:end);
%    d1=d(3:4:end)+j*d(4:4:end); % no used as long as no reference is recorded
    d1=d1-mean(d1);
    clear d
    if (longueur==4*fs)  
      puissance=max(fftshift(abs(fft(d1(1:1e5).^2))));
      if (puissance>1e9)
         freq=linspace(-fs/2,fs/2,length(d1));
         k=find((freq<-90000)&(freq>-100000));
         d22=fftshift(abs(fft(d1.^2))); % 0.1 Hz accuracy
         [~,tmp]=max(d22(k))
         df(p)=tmp+k(1)-1;df(p)=freq(df(p))/2;
         temps=[0:length(d1)-1]'/fs;
         lo=exp(-j*2*pi*df(p)*temps); % frequency offset
        
         y=d1.*lo;                      % frequency transposition
         prnmap01=ifft(fft(y).*fcode);  % correlation with returned signal
         [~,indice1(p)]=max(abs(prnmap01)); % only one correlation peak
      
         xval1(p)=prnmap01(indice1(p));
         xval1m1(p)=prnmap01(indice1(p)-1);
         xval1p1(p)=prnmap01(indice1(p)+1);
         [u,v]=polyfit([-1:+1]',abs(prnmap01([indice1(p)-1:indice1(p)+1])),2);
         correction1(p)=-u(2)/2/u(1);
      else
        printf("NG\n")
      end
    end
    p=p+1
  until (longueur<4*fs);
fclose(f)
      
solution1=indice1+correction1;
plot((solution1)/fs); % ranging solution
nom=strrep(filelist(filenum).name,'.bin','.mat');
% eval(['save -mat ',nom,' xv* corr* df indic*']);
clear xv* corr* df indic*
end
