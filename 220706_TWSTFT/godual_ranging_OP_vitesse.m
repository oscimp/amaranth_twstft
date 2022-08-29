pkg load signal

fs=5e6;
vitesse=-3.25e-9;

f=fopen('OP_prn22bpskcode0.bin');
code=fread(f,inf,'int8');
code=repelems(code,[[1:length(code)] ; ones(1,length(code))*2]); % interpolate
code=code-mean(code);
fcode=conj(fft(code'));
fclose(f);

filelist=dir('./OP11h45.bin');
for filenum=1:length(filelist)
  filelist(filenum).name
  f=fopen(filelist(filenum).name);
  
  p=1;
  t0=0;
  dt=0;
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
    k=find((freq<106200)&(freq>96200));
    d22=fftshift(abs(fft(d1.^2))); % 0.1 Hz accuracy
    [~,df(p)]=max(d22(k));df(p)=df(p)+k(1)-1;df(p)=freq(df(p))/2;df(p)
    temps=[0:length(d1)-1]'/fs;
    lo=exp(-j*2*pi*df(p)*temps); % frequency offset
  
    y=d1.*lo;                      % frequency transposition

    yi=interp1([0:length(y)-1],y,[0:length(y)-1]*1/(1-vitesse)+t0).';
    t0=t0+length(y)*vitesse
    if (isnan(yi(end))) yi(end)=yi(end-1);end
    if (isnan(yi(1))) yi(1)=yi(2);end
% voir en fin de boucle pour la manipulation de t0 et dt

    prnmap01=ifft(fft(yi).*fcode);  % correlation with returned signal
    prnmap02=ifft(fft(d2).*fcode); % correlation with reference signal
    [~,indice1(p)]=max(abs(prnmap01)); % only one correlation peak
    [~,indice2(p)]=max(abs(prnmap02)); % only one correlation peak
printf("%f %f\n",indice1(p),indice2(p))
    xval1(p)=prnmap01(indice1(p));
    xval2(p)=prnmap02(indice2(p));
    xval1m1(p)=prnmap01(indice1(p)-1);
    xval1p1(p)=prnmap01(indice1(p)+1);
    xval2m1(p)=prnmap02(indice2(p)-1);
    xval2p1(p)=prnmap02(indice2(p)+1);
    [u,v]=polyfit([-1:+1]',abs(prnmap01([indice1(p)-1:indice1(p)+1])),2);
    correction12(p)=-u(2)/2/u(1);
%    [u,v]=polyfit([-2:+2]',abs(prnmap01([indice1(p)-2:indice1(p)+2])),3);
%    delta=4*u(2)^2-12*u(1)*u(3)
%    correction13a(p)=(-2*u(2)+sqrt(delta))/6/u(1);
%    correction13b(p)=(-2*u(2)-sqrt(delta))/6/u(1);
    [u,v]=polyfit([-1:+1]',abs(prnmap02([indice2(p)-1:indice2(p)+1])),2);
    correction22(p)=-u(2)/2/u(1);
%    [u,v]=polyfit([-2:+2]',abs(prnmap02([indice2(p)-2:indice2(p)+2])),3);
%    delta=4*u(2)^2-12*u(1)*u(3)
%    correction23a(p)=(-2*u(2)+sqrt(delta))/6/u(1);
%    correction23b(p)=(-2*u(2)-sqrt(delta))/6/u(1);

indice1(p)=indice1(p)+dt;
% doit etre apres indice1(p)
    if (t0>=1) t0=t0-1;dt=dt-1;end
    if (t0<=-1) t0=t0+1;dt=dt+1;end
    p=p+1;
end
  until (longueur<4*fs);
%  until (p==40);
  solution12=indice1+correction12;
  solution22=indice2+correction22;
%  solution13=indice1+correction13b;
%  solution23=indice2+correction23b;
  subplot(211)
  plot((solution12-solution22)/fs); % ranging solution
%  hold on
%  plot((solution13-solution23)/fs); % ranging solution
  xlabel('time (s)')
  ylabel('ranging delay (s)')
  [a,b]=polyfit([1:length(solution12)],(solution12-solution22)/fs,1);
  subplot(212)
  plot((solution12-solution22)/fs-b.yf); % ranging solution
  hold on
  std((solution12-solution22)/fs-b.yf)
  mean((solution12-solution22)/fs-b.yf)
%  [a,b]=polyfit([1:length(solution13)],(solution13-solution23)/fs,1);
  subplot(212)
%  plot((solution13-solution23)/fs-b.yf); % ranging solution
%  std((solution13-solution23)/fs-b.yf)
%  mean((solution13-solution23)/fs-b.yf)
%  legend(num2str(std((solution13-solution23)/fs-b.yf)))
  xlabel('time (s)')
  ylabel('delay - parabolic fit (s)')
  nom=strrep(filelist(filenum).name,'.bin','.mat');
%  eval(['save -mat ',nom,' xv* corr* df indic*']);
%  clear xv* corr* df indic*
  fclose(f)
end

