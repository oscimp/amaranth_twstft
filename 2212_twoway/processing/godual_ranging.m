pkg load signal
% graphics_toolkit('gnuplot')

fs=5e6;
Nint=1;

dirlist=dir('./*bin')
dirbit=dir('./code/*bin')
for dirnum=1:length(dirlist)
  dirbit(mod(dirnum-1,length(dirbit))+1).name
  f=fopen(['code/',dirbit(mod(dirnum-1,length(dirbit))+1).name]);
  code=fread(f,inf,'int8');
  code=repelems(code,[[1:length(code)] ; ones(1,length(code))*2]); % interpolate
  code=2*code-1;  % +1/-1
  fcode=conj(fft(code'));
  fclose(f);

  dirlist.name
  f=fopen(dirlist(dirnum).name);
  
  p=1;
  do
    d=fread(f,length(fcode)*4,'int16');  % 1 code length
    longueur=length(d);
    d=d(1:2:end)+j*d(2:2:end);
    d1=d(1:2:end);  % measurement
    d2=d(2:2:end);  % reference
    d1=d1-mean(d1);
    d2=d2-mean(d2);
    clear d
  %  x1avant=abs(xcorr(d1,code));x1avant=x1avant(length(code):end);
    if (longueur==length(fcode)*4)  
      freq=linspace(-fs/2,fs/2,length(d1));
      k=find((freq<106200)&(freq>-96200));
  %%% d1
      d22=fftshift(abs(fft(d1.^2))); % 0.1 Hz accuracy
      [~,df1(p)]=max(d22(k));df1(p)=df1(p)+k(1)-1;df1(p)=freq(df1(p))/2;offset1=df1(p);
      temps=[0:length(d1)-1]'/fs;
      lo=exp(-j*2*pi*df1(p)*temps); % frequency offset
    
      y=d1.*lo;                      % frequency transposition
  % the phase of the correlation can be found to identify the oscillator drift but not before correlation at low SNR!
      prnmap01=fftshift(fft(y).*fcode);      % xcorr
      if (p==fs/length(code)*10) % after 10 s
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
      yf=fftshift(fft(y));
      yint=[zeros(length(y)*(Nint),1) ; yf ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
      yint=(ifft(fftshift(yint)));       % back to time /!\ outer fftshift for 0-delay at center
      codetmp=repelems(code,[[1:length(code)] ; ones(1,length(code))*(2*Nint+1)])'; % interpolate
      yincode=[yint(indice1(p)-1:end) ; yint(1:indice1(p)-2)].*codetmp;
      SNR1r(p)=mean(real(yincode))^2/var(yincode);
      SNR1i(p)=mean(imag(yincode))^2/var(yincode);
  %    cf=fftshift(fft(code));
  %    cint=[zeros(length(code)*(Nint),1) ; cf.' ; zeros(length(code)*(Nint),1)]; % interpolation to 3x samp_rate
  %    cint=real((ifft(fftshift(cint))));       % back to time /!\ outer fftshift for 0-delay at center
  
  %%% d2
      d22=fftshift(abs(fft(d2.^2))); % 0.1 Hz accuracy
      [~,df2(p)]=max(d22(k));df2(p)=df2(p)+k(1)-1;df2(p)=freq(df2(p))/2;offset2=df2(p);
      temps=[0:length(d2)-1]'/fs;
      lo=exp(-j*2*pi*df2(p)*temps); % frequency offset
    
      y=d2.*lo;                      % frequency transposition
      prnmap02=fftshift(fft(y).*fcode);      % xcorr
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
  % SNR computation
      yf=fftshift(fft(y));
      yint=[zeros(length(y)*(Nint),1) ; yf ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
      yint=(ifft(fftshift(yint)));       % back to time /!\ outer fftshift for 0-delay at center
      yincode=[yint(indice2(p)-1:end) ; yint(1:indice2(p)-2)].*codetmp;
      SNR2r(p)=mean(real(yincode))^2/var(yincode);
      SNR2i(p)=mean(imag(yincode))^2/var(yincode);
      if (p==fs/length(code)*10) % after 10 s
         figure
         plot(angle([yint(indice2(p)-1:end) ; yint(1:indice2(p)-2)]))
         xlim([0 1200])
         hold on
         plot(codetmp)
         pause(0.1)
      end
      printf("%d\t%f\t%f\t%f\t%f\t%f\r\n",p,offset1,10*log10(SNR1i(p)+SNR1r(p)),offset2,10*log10(SNR2i(p)+SNR2r(p)),(indice1(p)+correction1_a(p)-indice2(p)-correction2_a(p))/fs/(2*Nint+1))
      p=p+1;
    end
  until (longueur<length(fcode)*4);
  fclose(f)
  solution1=indice1+correction1_a;
  solution2=indice2+correction2_a;
  subplot(211)
  plot((solution1)/(2*Nint+1)/fs); % ranging solution
  xlabel('time (s)')
  ylabel('ranging delay (s)')
  [a,b]=polyfit([1:length(solution1)],(solution1)/(2*Nint+1)/fs,2);
  subplot(212)
  plot((solution1)/(2*Nint+1)/fs-b.yf); % ranging solution
  std((solution1)/(2*Nint+1)/fs-b.yf)
  mean((solution1)/(2*Nint+1)/fs-b.yf)
  legend(num2str(std((solution1)/(2*Nint+1)/fs-b.yf)))
  xlabel('time (s)')
  ylabel('delay - parabolic fit (s)')
  nom=strrep(dirlist(dirnum).name,'.bin','.mat');
  eval(['save -mat /tmp/',nom,' xv* corr* df1 df2 indic* SNR* code']);
  clear xv* corr* df* indic* p SNR*
end
