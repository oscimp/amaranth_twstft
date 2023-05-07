pkg load control
pkg load signal
close all
clear all

fs=5e6
OP=0
position=1 % 2 pour local, 1 pour remote

filename='../../230412_100kchips_with_code/1681305121.bin';
taille=dir(filename).bytes;
duree_totale=taille/8/fs; % short=2 ; complex=2 ; 2 channels

filedesc=fopen (filename, 'rb');
fread(filedesc,fs*8*6,'int16');         % remove 6s

x=fread(filedesc, 4*fs/10, 'int16');
x=x(1:2:end)+j*x(2:2:end);
x=x(position:2:end);
fclose(filedesc);

% PRN definition
codelocation='../../221207_twoway_codes/codes/'
dirbit=dir([codelocation,'/n*.bin']);
nom=dirbit(1+OP).name  % LTFB=odd OP=even
f=fopen([codelocation,'/',nom]);
code=fread(f,inf,'int8');
ap=repelems(code,[[1:length(code)] ; ones(1,length(code))*2]); % interpolate
ap=2*ap-1;  % +1/-1
fclose(f);
al=[ap(end) ap(1:end-1)];
ae=[ap(2:end) ap(1)];

% frequency offset identification
Nb_points=duree_totale*(fs/length(code)/2);
freq=linspace(-fs/2,fs/2,fs/10);
s=abs(fftshift(fft(x.^2)));
[a,b]=max(s);freq0=freq(b)/2
points_per_code=length(ap);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
time=[0:points_per_code-1]'/fs;

alpha=0.001;beta=0.0031;   % 3200
alpha=0.001;beta=0.0081;   % 1570
alpha=0.001;beta=0.0021;   % 4050 (pquoi pas sauts de pi ?)
alpha=0.001;beta=0.0011;   % NG
alpha=0.002;beta=0.0021;   % NG
alpha=0.001;beta=0.0081;   % 1600
alpha=0.001;beta=0.0021;   % sauts de pi
alpha=0.00051;beta=0.0081; % oscille
alpha=0.011;beta=0.0081;   % 550
alpha=0.001;beta=0.0051;   % 2200 x2
coef_uk_1 = 2;
coef_uk_2 = -1;
coef_ek = alpha+beta;
coef_ek_1 = -alpha;

%TEST
  alpha=0.05/6;
  coef_uk_1 = 1;
  coef_uk_2 = 0;
  coef_ek = alpha;
  coef_ek_1 = 0;
%END TEST


% initialisation des variables pour la vitesse de calcul
fr=NaN(Nb_points,1);
yp=NaN(Nb_points,1);
yyp=NaN(Nb_points,1);
u=NaN(Nb_points,1);
k=NaN(Nb_points,1);
  
% quelques initialisations  
k(1)=0;
freq=0;
fr(1)=0;
freqm1=freq;
freqm2=freqm1;
ym1=0;

l=1;
MAXLAG=points_per_code;

filedesc=fopen (filename, 'rb');
fread(filedesc,fs*8*6,'int16');         % remove 6s
x=fread(filedesc, 4*points_per_code, 'int16');
x=x(1:2:end)+j*x(2:2:end);
x=x(position:2:end);
xx=x.*exp(1j*(2*pi*(-freq0)*time));
zp=xcorr(ap,xx); 

figure(1)
plot(abs(zp)');
title('intercorelation initiale')
[aap,bbp]=max(abs(zp))
bbp=bbp-length(zp)/2;

if (bbp>0)
  x=x(points_per_code-bbp:end);
  manquant=length(ap)-length(x);
  xx=fread(filedesc, 4*manquant, 'int16');
  xx=xx(1:2:end)+j*xx(2:2:end);
  xx=xx(position:2:end);
  x=[x ; xx];
else
  x=x(-bbp:end);
  manquant=length(ap)-length(x);
  xx=fread(filedesc, 4*manquant, 'int16');
  xx=xx(1:2:end)+j*xx(2:2:end);
  xx=xx(position:2:end);
  x=[x ; xx];
end

zp=xcorr(ap,xx); 
plot(abs(zp)');
title('deuxième intercorelation')

do % boucle principale
  xx=fread(filedesc, 4*points_per_code, 'int16');
  longueur=length(xx);
  x=xx(1:2:end)+j*xx(2:2:end);
  x=x(position:2:end);
  time=time(end)+[1:length(x)]'/fs; % temps continue avec increment de 1/fs
  mysine=exp(1j*(2*pi*(-freq0+freq)*time)); 
  xx=x.*mysine;  
  zl=xcorr(al,xx,MAXLAG); 
  zp=xcorr(ap,xx,MAXLAG); 
  ze=xcorr(ae,xx,MAXLAG); 
  
  if (mod(l,100)==0)
    figure(3)
    subplot(311)
    plot([abs(zl)' abs(zp)' abs(ze)']);
    legend( 'late','prompt','early');
    subplot(312)
    kk=find(isnan(fr)==0);
    plot(fr(kk))
    subplot(313)
    kkk=find(yyp<-1);yyp(kkk)=yyp(kkk)+2*pi;
    plot(yyp(kk))
    figure(4)
    subplot(312)
    plot(u(kk))
    subplot(313)
    plot(yp(kk))
    pause(0.1)
  end
  [aal,bbl]=max(abs(zl));
  [aap,bbp(l)]=max(abs(zp));
  [aae,bbe]=max(abs(ze));
    
  %discrimanateur cohérent : kai borre p99
  d(l)=(abs(ze(bbe)^2)-abs(zl(bbl))^2)/(abs(ze(bbe))^2+abs(zl(bbl))^2);

  MAXLAG=20;
  if d(l)<-0.5
    ap=[ap(end) ap(1:end-1)];
    al=[ap(end) ap(1:end-1)];
    ae=[ap(2:end) ap(1)];
  end
  if d(l)>0.5
    ap=[ap(2:end) ap(1)];
    al=[ap(end) ap(1:end-1)];
    ae=[ap(2:end) ap(1)];
  end

  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  [u(l),k(l)]=max(abs(zp));
  yp(l)=atan(imag(zp(k(l)))./real(zp(k(l))));  
  yyp(l)=atan2(imag(zp(k(l))),real(zp(k(l))));  
  freq=coef_uk_1*freqm1+coef_uk_2*freqm2+coef_ek*yp(l)+coef_ek_1*ym1;
  fr(l)=freq;
  freqm2=freqm1;
  freqm1=freq;
  ym1=yp(l);
  l=l+1
until (longueur<2*points_per_code);
moyenne=mean(yp(2000:end-2))
ecart_type=std(yp(2000:end-2))
