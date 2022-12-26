pkg load signal
% graphics_toolkit('gnuplot')
affiche=0;
fs=5e6;
Nint=1;
remote=0
OP=0
debug=1
datalocation='./'
if (debug != 1)
  codelocation='./codes/'
else
  codelocation='./'
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

  dirlist(dirnum).name           % (dirnum)
  eval(["f=fopen('",datalocation,"/",dirlist(dirnum).name,"');"]); % (dirnum)
  
  p=1;
  printf("n\tdt1\tdf1\tP1\tSNR1\tdt2\tdf2\tP2\tSNR2\r\n");
  do
    d=fread(f,length(fcode)*4,'int16');  % 1 code length
    longueur=length(d);
    d=d(1:2:end)+j*d(2:2:end);
    d1=d(1:2:end);  % measurement
    d2=d(2:2:end);  % reference
    d1=d1-mean(d1);
    d2=d2-mean(d2);
    if (OP==1)
%       tmp=d1;
%       d1=d2;
%       d2=tmp;
    end
    clear d
  %  x1avant=abs(xcorr(d1,code));x1avant=x1avant(length(code):end);
    if (longueur==length(fcode)*4)  
      freq=linspace(-fs/2,fs/2,length(d1));
      if (remote!=1)
         k=find((freq<20000)&(freq>-20000));
      else
         if (OP==1)
            k=find((freq>-120000)&(freq<-80000)); % -50 kHz
         else
            k=find((freq<120000)&(freq>80000));
         end
      end
  %%% d1
      d22=fftshift(abs(fft(d1.^2))); % 0.1 Hz accuracy
      [~,df1(p)]=max(d22(k));df1(p)=df1(p)+k(1)-1;df1(p)=freq(df1(p))/2;offset1=df1(p);
      temps=[0:length(d1)-1]'/fs;
      if (abs(df1(p))<(freq(2)-freq(1))) df1(p)=0;end;
      lo=exp(-j*2*pi*df1(p)*temps); % frequency offset
    
      y=d1.*lo;                      % frequency transposition
  % the phase of the correlation can be found to identify the oscillator drift but not before correlation at low SNR!
      ffty=fft(y);
      prnmap01=fftshift(ffty.*fcode);      % xcorr
      if ((p==fs/length(code)*10) && (affiche==1))% after 10 s
         figure
         plot(abs(ifft(fftshift(prnmap01))))
         xlabel('offset (index)');ylabel('xcorr (a.u.)')
      end
      prnmap01=[zeros(length(y)*(Nint),1) ; prnmap01 ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
      prnmap01=(ifft(fftshift(prnmap01)));       % back to time /!\ NO outer fftshift for 0-delay at left
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
      correction1_a(p)=(abs(prnmap01(indice1(p)-1))-abs(prnmap01(indice1(p)+1)))/(abs(prnmap01(indice1(p)-1))+abs(prnmap01(indice1(p)+1))-2*abs(prnmap01(indice1(p))))/2;
  % SNR computation
%      yf=fftshift(fft(y));
%      yint=[zeros(length(y)*(Nint),1) ; yf ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
%      yint=(ifft(fftshift(yint)));       % back to time /!\ outer fftshift for 0-delay at center
      yint=zeros(length(y)*(2*Nint+1),1);
      yint(1:length(y)/2)=ffty(1:length(y)/2);
      yint(end-length(y)/2+1:end)=ffty(length(y)/2+1:end);
      yint=ifft(yint);
      codetmp=repelems(code,[[1:length(code)] ; ones(1,length(code))*(2*Nint+1)])'; % interpolate
      yincode=[yint(indice1(p)-1:end) ; yint(1:indice1(p)-2)].*codetmp;
      SNR1r(p)=mean(real(yincode))^2/var(yincode);
      SNR1i(p)=mean(imag(yincode))^2/var(yincode);
      puissance1total(p)=var(y);
      puissance1code(p)=mean(real(yincode))^2+mean(imag(yincode))^2;

  %    cf=fftshift(fft(code));
  %    cint=[zeros(length(code)*(Nint),1) ; cf.' ; zeros(length(code)*(Nint),1)]; % interpolation to 3x samp_rate
  %    cint=real((ifft(fftshift(cint))));       % back to time /!\ outer fftshift for 0-delay at center
  
  %%% d2
      if (remote!=1)
        d22=fftshift(abs(fft(d2.^2))); % 0.1 Hz accuracy
        [~,df2(p)]=max(d22(k));df2(p)=df2(p)+k(1)-1;df2(p)=freq(df2(p))/2;offset2=df2(p);
        temps=[0:length(d2)-1]'/fs;
        if (abs(df2(p))<(freq(2)-freq(1))) df2(p)=0;end;
        lo=exp(-j*2*pi*df2(p)*temps); % frequency offset
      
        y=d2.*lo;                      % frequency transposition
        ffty=fft(y);
        prnmap02=fftshift(ffty.*fcode);      % xcorr
        prnmap02=[zeros(length(y)*(Nint),1) ; prnmap02 ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
        prnmap02=(ifft(fftshift(prnmap02)));       % back to time
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
        correction2_a(p)=(abs(prnmap02(indice2(p)-1))-abs(prnmap02(indice2(p)+1)))/(abs(prnmap02(indice2(p)-1))+abs(prnmap02(indice2(p)+1))-2*abs(prnmap02(indice2(p))))/2;
        if ((p==fs/length(code)*10) && (affiche==1)) % after 10 s
           plot(abs(prnmap01(indice1(p)-2:indice1(p)+2)))
           hold on
           plot(abs(prnmap02(indice2(p)-2:indice2(p)+2)))
           indice1(p)
           indice2(p)
        end
    % SNR computation
%       yf=fftshift(fft(y));
%       yint=[zeros(length(y)*(Nint),1) ; yf ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
%       yint=(ifft(fftshift(yint)));       % back to time /!\ outer fftshift for 0-delay at center
        yint=zeros(length(y)*(2*Nint+1),1);
        yint(1:length(y)/2)=ffty(1:length(y)/2);
        yint(end-length(y)/2+1:end)=ffty(length(y)/2+1:end);
        yint=ifft(yint);
        yincode=[yint(indice2(p)-1:end) ; yint(1:indice2(p)-2)].*codetmp;
%        if (debug==1)
%           format long
%           indice2(p)
%           yrotate=[yint(indice2(p)-1:end) ; yint(1:indice2(p)-2)];
%           save -mat debug.mat yrotate codetmp
%           exit
%        end
        SNR2r(p)=mean(real(yincode))^2/var(yincode);
        SNR2i(p)=mean(imag(yincode))^2/var(yincode);
        puissance2total(p)=var(y);
        puissance2code(p)=mean(real(yincode))^2+mean(imag(yincode))^2;
        if ((p==fs/length(code)*10) && (affiche==1)) % after 10 s
           figure
           plot(angle([yint(indice2(p)-1:end) ; yint(1:indice2(p)-2)]))
           xlim([0 1200])
           hold on
           plot(codetmp)
           pause(0.1)
        end
        printf("%d\t%.12f\t%.3f\t%.1f\t%.1f\t%.12f\t%.3f\t%.1f\t%.1f\r\n",p,(indice1(p)+correction1_a(p))/fs/(2*Nint+1),offset1,10*log10(puissance1total(p)),10*log10(SNR1i(p)+SNR1r(p)),(indice2(p)-correction2_a(p))/fs/(2*Nint+1),offset2,10*log10(puissance2total(p)),10*log10(SNR2i(p)+SNR2r(p)))
      else
        printf("%d\t%.12f\t%.3f\t%.1f\t%.1f\r\n",p,(indice1(p)+correction1_a(p))/fs/(2*Nint+1),offset1,10*log10(puissance1total(p)),10*log10(SNR1i(p)+SNR1r(p)))
      end
      p=p+1;
    end
  until (longueur<length(fcode)*4);
  fclose(f)
  solution1=indice1+correction1_a;
  if (remote!=1)
    solution2=indice2+correction2_a;
  end
  [a,b]=polyfit([1:length(solution1)],(solution1)/(2*Nint+1)/fs,2);
  std((solution1)/(2*Nint+1)/fs-b.yf)
  mean((solution1)/(2*Nint+1)/fs-b.yf)

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
    eval(['save -mat ',datalocation,'/',nom,' xv* corr* df1 df2 indic* SNR* code puissan*']);
  else
    eval(['save -mat ',datalocation,'/remote',nom,' xv* corr* df1 indic* SNR* code puissa*']);
  end
  clear xv* corr* df* indic* p SNR* puissa*
end
