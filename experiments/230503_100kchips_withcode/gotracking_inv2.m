pkg load control
pkg load signal
close all
clear all

fs=5e6
OP=0
position=1 % 2 pour local, 1 pour remote

n_sommes=0;
%b=0.25   % l'IT simple 
%b=0.005 % l'IT double
b=0    % en test

filename=dir('./data_OP/*bin');
filename=filename(1);
taille=dir(filename).bytes;
duree_totale=taille/8/fs; % short=2 ; complex=2 ; 2 channels

filedesc=fopen (filename, 'rb');
fread(filedesc,fs*8*6,'int16');         % remove 6s

x=fread(filedesc, 4*fs/10, 'int16');
x=x(1:2:end)+j*x(2:2:end);
x=x(position:2:end);
fclose(filedesc);

% PRN definition
codelocation='./'
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
time=[0:1/fs:(length(x)-1)/fs]';

% correcteur "minimum" 1 IT pur -> erreur statique
 Te=40e-3;  % JMF : 0.01 -> 0.1
 Cz=zpk([0],[1],0.01,Te); % gros dépassement mais phase nulle puis "diverge" 
 gamma=0;

 % mise en place des données pour l'équation récurente
  [num,den]=tfdata(Cz,'v');
  num=[num zeros(1,4)]; 
  den=[den zeros(1,4)];

  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  % Correcteur du PRN
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  
  % aa=0.90;100*(1-aa)   beta=1; JMF valeur initiale 0.9
  aa=0.90;   beta=1;
  Cz_PRN=tf([100*(1-aa)],conv([1 -1],[1 -aa]),Te); % reproduction de l'existant (gotracking_inv)  
  % s(l+1)=aa*s(l)+d(l)*(1-aa); 
  [num_PRN,den_PRN]=tfdata(Cz_PRN,'v');
  num_PRN=[num_PRN zeros(1,4)]; 
  den_PRN=[den_PRN zeros(1,4)];  
  
  % initialisation des variables pour la vitesse de calcul
  fr=NaN(Nb_points,1);
  yp=NaN(Nb_points,1);
  yyp=NaN(Nb_points,1);
  u=NaN(Nb_points,1);
  k=NaN(Nb_points,1);
  cf=NaN(Nb_points,1);
  N_P=100;
  yp_back=zeros(N_P,1);
  fr_back=zeros(N_P,1);
  
% quelques initialisations  
  cf(1)=0;
  dkk=zeros(Nb_points,1);
  s=zeros(Nb_points,1);
  k(1)=0;
  
freq=0;

l=1;
MAXLAG=points_per_code;

filedesc=fopen (filename, 'rb');
fread(filedesc,fs*8*6,'int16');         % remove 6s
x=fread(filedesc, 4*points_per_code, 'int16');
x=x(1:2:end)+j*x(2:2:end);
x=x(position:2:end);
% JMF xx=x(1:points_per_code).*exp(1j*(2*pi*mod( ((freq0)*time(1:points_per_code)),1)));  
xx=x.*exp(1j*(2*pi*(-freq0)*time(1:points_per_code)));
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
xx=x(1:points_per_code).*exp(1j*(2*pi*(-freq0)*time(1:points_per_code)));  
zp=xcorr(ap,xx); 

figure
  zp=xcorr(ap,xx,20); 
  plot(abs(zp)');
  title('deuxième intercorelation')
  %pause
  [aap,bbp]=max(abs(zp))
  mysine_sum=[];
  phi(l)=0;
  % boucle principale


# Set tracking loop parameters
T_blk = 80e-3                        # tracking block duration / integration period (s)
delay_spacing = 0.5                 # DLL correlator delay spacing
# Define tracking loop bandwidths
B_DLL = 2
B_PLL = 20
code_phase=0
carrier_phase=0;
doppler_freq=0;
    zeta = 1 / sqrt(2);
    omega_n = B_PLL / .53;
do
  xx=fread(filedesc, 4*points_per_code, 'int16');
  longueur=length(xx);
  x=xx(1:2:end)+j*xx(2:2:end);
  x=x(position:2:end);
  time=time(end)+[1:length(x)]'/fs; % temps continue avec increment de 1/fs
  mysine=exp(1j*(2*pi*(-freq0+doppler_freq(l))*time)); 

  xx=x.*mysine;  
  
  zl=xcorr(al,xx,MAXLAG); 
  zp=xcorr(ap,xx,MAXLAG); 
  ze=xcorr(ae,xx,MAXLAG); 

  if (mod(l,250)==0)
    figure(3)
subplot(311)
    plot([abs(zl)' abs(zp)' abs(ze)']); legend( 'late','prompt','early');
subplot(312)
    plot(fr)
subplot(313)
    plot(yyp)
    % figure(2); plot(cf)
  end
  [aal,bbl]=max(abs(zl));
  [aap,bbp(l)]=max(abs(zp));
  [aae,bbe]=max(abs(ze));
    
  %discrimanateur cohérent
  % kai borre p99

    ### DLL ###
    # 1) Compute code phase error using early-minus-late discriminator
    code_phase_error(l)=delay_spacing*(abs(ze(bbe))-abs(zl(bbl)))/(abs(ze(bbe))+abs(zl(bbl))+2*abs(zp(bbp(l))));
    
    # 2) Filter code phase error to reduce noise
    #  We implement the DLL filter by updating code phase in proportion to code
    #  phase dicriminator output.  The result has the equivalentresponse of a
    #  1st-order DLL filter
    filtered_code_phase_error = T_blk * B_DLL / .25 * code_phase_error(l);
    
    measured_code_phase = code_phase + code_phase_error(l);
    filtered_code_phase = code_phase + filtered_code_phase_error;
    
    ### PLL ###
    # 1) Compute phase error (in cycles) using appropriate phase discriminator
    delta_theta(l) = atan(imag(zp(bbp(l))) / real(zp(bbp(l)))) / (2 * pi);
    sortie(l) = atan2(imag(zp(bbp(l))) , real(zp(bbp(l)))) / (2 * pi);
    carrier_phase_error = delta_theta(l);
    doppler_freq_error = T_blk / 2 * delta_theta(l)
    
    # 2) Filter carrier phase error to reduce noise
    #  We implement the PLL filter by updating carrier phase and frequency in
    #  proportion to the phase discriminator output in a way that has the
    #  equivalent response to a 2nd-order PLL filter
    filtered_carrier_phase_error = (2 * zeta * omega_n * T_blk - 3 / 2 * omega_n^2 * T_blk^2) * delta_theta(l);
    filtered_doppler_freq_error = omega_n^2 * T_blk * delta_theta(l);
    
    measured_carrier_phase = carrier_phase + carrier_phase_error;
    filtered_carrier_phase = carrier_phase + filtered_carrier_phase_error;
    
    measured_doppler_freq = doppler_freq(l) + doppler_freq_error;
    filtered_doppler_freq = doppler_freq(l) + filtered_doppler_freq_error;
    
    # Update to next time epoch (this step is considered part of the loop filter!)
    code_phase = filtered_code_phase;
    carrier_phase = filtered_carrier_phase;
    
    #  Here we apply carrier-aiding by adjusting `f_code` based on Doppler frequency
%    f_code_adj = signal.f_code * (1 + doppler_freq / signal.f_carrier)
%    code_phase += f_code_adj * T_blk
%    f_inter = signal.f_carrier - f_center
%    carrier_phase += (f_inter + doppler_freq) * T_blk

if (mod(l,250)==0)
  subplot(311)
  plot(delta_theta)
  subplot(312)
  plot(sortie)
  subplot(313)
  plot(doppler_freq)
end

l=l+1;
    doppler_freq(l) = filtered_doppler_freq;
%%%%% FIN FIN FIN
until  (longueur<2*points_per_code);

figure
subplot(211)
plot((yp),'r.');
grid
subplot(212)
%plot((yyp),'r.');
plot(fr,'r.')
title('phase et frequence');

moyenne=mean(yp(points_per_code:end-2))
ecart_type=std(yp(points_per_code:end-2))

I=find(yyp<-pi/2)
yyp(I)=yyp(I)+2*pi;
plot(yyp)


%%%%%%%%%%%%%%

