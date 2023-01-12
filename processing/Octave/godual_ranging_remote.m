pkg load signal
% graphics_toolkit('gnuplot')
global temps freq fcode code fs Nint    % save time by avoiding unnecessary fixed parameter arguments
fs=5e6;
Nint=1;
remote=1
OP=0
affiche=0;
debug=1
datalocation='./'

function [indice,correction,SNRr,SNRi,df,puissance,puissancecode,puissancenoise]=processing(d,k)
      global temps freq fcode code fs Nint
      d2=fftshift(abs(fft(d.^2))); % 0.5 Hz accuracy
      [~,df]=max(d2(k));df=df+k(1)-1;df=freq(df)/2;offset=df;
      % if (abs(df1(p))<(freq(2)-freq(1))) df1(p)=0;end;
      lo=exp(-j*2*pi*df*temps);         % coarse frequency offset
      y=d.*lo;                          % coarse frequency transposition
% addition 221228: fine frequency from phase drift
      [a,b]=polyfit([1:10:fs/3]'/fs,conv(angle(y(1:10:fs/3)),ones(100,1)/100)(50:end-50),1);
      dfleftover=a(1)/2/pi;             % fine frequency correction
      lo=exp(-j*2*pi*dfleftover*temps); % frequency offset
      y=y.*lo;                          % frequency transposition
      df+=dfleftover;
      ffty=fft(y);
      prnmap=fftshift(ffty.*fcode);     % xcorr
      prnmap=[zeros(length(y)*(Nint),1) ; prnmap ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
      prnmap=(ifft(fftshift(prnmap)));  % back to time /!\ NO outer fftshift for 0-delay at left
      [~,indice]=max(abs(prnmap));
      xval=prnmap(indice);
      xvalm1=prnmap(indice-1);
      xvalp1=prnmap(indice+1);
      correction=(abs(xvalm1)-abs(xvalp1))/(abs(xvalm1)+abs(xvalp1)-2*abs(xval))/2;
% SNR computation
%      yf=fftshift(fft(y));
%      yint=[zeros(length(y)*(Nint),1) ; yf ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
%      yint=(ifft(fftshift(yint)));       % back to time /!\ outer fftshift for 0-delay at center
      yint=zeros(length(y)*(2*Nint+1),1);
      yint(1:length(y)/2)=ffty(1:length(y)/2);
      yint(end-length(y)/2+1:end)=ffty(length(y)/2+1:end);
      yint=ifft(yint);
      codetmp=repelems(code,[[1:length(code)] ; ones(1,length(code))*(2*Nint+1)])'; % interpolate
      yincode=[yint(indice-1:end) ; yint(1:indice-2)].*codetmp;
      SNRr=mean(real(yincode))^2/var(yincode);
      SNRi=mean(imag(yincode))^2/var(yincode);
      puissance=var(y);
      puissancecode=mean(real(yincode))^2+mean(imag(yincode))^2;
      puissancenoise=var(yincode);
end

if (debug != 1)
  codelocation='./codes/'
else
  codelocation='./codes/'
end

dirlist=dir([datalocation,'/1*.bin']);
dirbit=dir([codelocation,'/n*.bin']);
for dirnum=1:length(dirlist)
  nom=dirbit(mod(OP+remote,2)+1).name  % LTFB=odd OP=even
  % OP=1, remote=0 or OP=0, remote=1 => even ; OP=0, remote=0 or OP=1, remote=1 => odd
  f=fopen([codelocation,'/',nom]);
  code=fread(f,inf,'int8');
  code=repelems(code,[[1:length(code)] ; ones(1,length(code))*2]); % interpolate
  code=2*code-1;  % +1/-1
  fcode=conj(fft(code'));
  fclose(f);

  dirlist(dirnum).name
  eval(["f=fopen('",datalocation,"/",dirlist(dirnum).name,"');"]);
  p=1;
  temps=[0:length(code)-1]'/fs;
  freq=linspace(-fs/2,fs/2,length(code));
  printf("n\tdt1\tdf1\tP1\tSNR1\tdt2\tdf2\tP2\tSNR2\r\n");
  do
    d=fread(f,length(fcode)*4,'int16');  % 1 code length
    longueur=length(d);
    d=d(1:2:end)+j*d(2:2:end);
    d1=d(1:2:end);  % measurement
    d1=d1-mean(d1);
    if (longueur==length(fcode)*4)  
      if (remote!=1)
         k=find((freq<20000)&(freq>-20000));
      else
         if (OP==1)
            k=find((freq>-120000)&(freq<-80000)); % -50 kHz
         else
            k=find((freq<120000)&(freq>80000));
         end
      end
    [indice1(p),correction1(p),SNR1r(p),SNR1i(p),df1(p),puissance1(p),puissance1code(p),puissance1noise(p)]=processing(d1,k);
    if (remote!=1)
        d2=d(2:2:end);  % reference
        d2=d2-mean(d2);
        [indice2(p),correction2(p),SNR2r(p),SNR2i(p),df2(p),puissance2(p),puissance2code(p),puissance2noise(p)]=processing(d2,k);
        printf("%d\t%.12f\t%.3f\t%.1f\t%.1f\t%.12f\t%.3f\t%.1f\t%.1f\r\n",p,(indice1(p)-1+correction1(p))/fs/(2*Nint+1),df1(p),10*log10(puissance1(p)),10*log10(SNR1i(p)+SNR1r(p)),(indice2(p)-1-correction2(p))/fs/(2*Nint+1),df2(p),10*log10(puissance2(p)),10*log10(SNR2i(p)+SNR2r(p)))
    else
        printf("%d\t%.12f\t%.3f\t%.1f\t%.1f\r\n",p,(indice1(p)-1+correction1(p))/fs/(2*Nint+1),df1(p),10*log10(puissance1(p)),10*log10(SNR1i(p)+SNR1r(p)))
    end
    p=p+1;
  end
  until (longueur<length(fcode)*4);
  fclose(f)
  solution1=indice1-1+correction1;
  if (remote!=1)
    solution2=indice2-1+correction2;
    [a,b]=polyfit([1:length(solution2)],(solution2)/(2*Nint+1)/fs,2); % should be flat: loopback channel
    std(solution2/(2*Nint+1)/fs-b.yf)
    mean(solution2/(2*Nint+1)/fs-b.yf)
  end
  [a,b]=polyfit([1:length(solution1)],(solution1)/(2*Nint+1)/fs,2);
  std(solution1/(2*Nint+1)/fs-b.yf)
  mean(solution1/(2*Nint+1)/fs-b.yf)

  if (affiche==1)
    subplot(211)
    plot((solution1)/(2*Nint+1)/fs); % ranging solution
    xlabel('time (s)')
    ylabel('ranging delay (s)')
    subplot(212)
    plot((solution1)/(2*Nint+1)/fs-b.yf); % ranging solution
    legend(num2str(std((solution1)/(2*Nint+1)/fs-b.yf)))
    xlabel('time (s)')
    ylabel('delay - parabolic fit (s)')
  end
  nom=strrep(dirlist(dirnum).name,'.bin','.mat');
  if (remote!=1)
    eval(['save -mat ',datalocation,'/',nom,' corr* df1 df2 indic* SNR* code puissan*']);
  else
    eval(['save -mat ',datalocation,'/remote',nom,' corr* df1 indic* SNR* code puissa*']);
  end
  clear corr* df* indic* p SNR* puissa*
end
