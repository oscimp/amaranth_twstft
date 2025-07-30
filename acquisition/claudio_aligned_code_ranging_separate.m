clear all
close all
pkg load signal
format long

% graphics_toolkit('gnuplot')
global temps freq fcode code fs Nint    % save time by avoiding unnecessary fixed parameter arguments
fs=5e6;
Nint=1;
remote=1
OP=getenv('OP')
datalocation=gentenv('processing_dir')
codelocation=getenv('codelocation')
remotechannel=getenv('remotechannel')
ls=2;
affiche=0;
debug=1
ranging=1

if (isempty('codelocation')) codelocation='/home/jmfriedt/codes/';end
if (isempty('OP')) OP=0;end
if (isempty('datalocation')) datalocation='./';end
if (isempty('remotechannel')) remotechannel=2';end % 1 or 2 => localchannel=3-remotechannel

function [xval,indice,correction,SNRr,SNRi,puissance,puissancecode,puissancenoise]=processing(d,k,df)
      global temps freq fcode code fs Nint
      % if (abs(df1(p))<(freq(2)-freq(1))) df1(p)=0;end;
      lo=exp(-j*2*pi*df*temps);         % coarse frequency offset
      y=d.*lo;                          % coarse frequency transposition
      ffty=fft(y);
%      prnmap=ifft(fcode.*conj(ffty));     % xcorr
%      [~,indice]=max(abs(prnmap));
%      xval=prnmap(indice);

      prnmap=fftshift(fcode.*conj(ffty));     % xcorr
      prnmap=[zeros(length(y)*(Nint),1) ; prnmap ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
      prnmap=(ifft(fftshift(prnmap)));  % back to time /!\ NO outer fftshift for 0-delay at left
      yint=zeros(length(y)*(2*Nint+1),1);
      yint(1:length(y)/2)=ffty(1:length(y)/2);
      yint(end-length(y)/2+1:end)=ffty(length(y)/2+1:end);
      yint=ifft(yint);
      codetmp=repelems(code,[[1:length(code)] ; ones(1,length(code))*(2*Nint+1)])'; % interpolate
      cm=1;
      for codeindex=1:length(code)*(2*Nint+1):length(prnmap)-length(code)*(2*Nint+1)+1
        [~,indice(cm)]=max(abs(prnmap(codeindex:codeindex+length(code)*(2*Nint+1)-1)));
        xval=prnmap(indice(cm)+codeindex-1);
        if ((indice(cm)+codeindex-1-1)>=1)
           xvalm1=prnmap(indice(cm)+codeindex-1-1);
        else
           xvalm1=prnmap(end);
        end
        if ((indice(cm)+codeindex-1+1)<length(prnmap))
           xvalp1=prnmap(indice(cm)+codeindex-1+1);
        else
           xvalp1=prnmap(1);
        end
        correction(cm)=(abs(xvalm1)-abs(xvalp1))/(abs(xvalm1)+abs(xvalp1)-2*abs(xval))/2;
% SNR computation
%      yf=fftshift(fft(y));
%      yint=[zeros(length(y)*(Nint),1) ; yf ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
%      yint=(ifft(fftshift(yint)));       % back to time /!\ outer fftshift for 0-delay at center
        yintmp=yint(codeindex:codeindex+length(code)*(2*Nint+1)-1);
%plot(angle(yintmp(1:2000))); 
%hold on
%plot(([codetmp(indice(cm)-1:end) ; codetmp(1:indice(cm)-2)])(1:2000));
        if (indice(cm)>2)
           yincode=[codetmp(indice(cm)-1:end) ; codetmp(1:indice(cm)-2)].*yintmp;
        else
           yincode=codetmp.*yintmp;
        end
        SNRr(cm)=mean(real(yincode))^2/var(yincode);
        SNRi(cm)=mean(imag(yincode))^2/var(yincode);
        puissance(cm)=var(y);
        puissancecode(cm)=mean(real(yincode))^2+mean(imag(yincode))^2;
        puissancenoise(cm)=var(yincode);
	cm=cm+1;
      end
end

dirlist=dir([datalocation,'/*_',num2str(remotechannel),'.bin']);
dirbit=dir([codelocation,'/n*.bin']);
for dirnum=1:length(dirlist)
  nomin=dirbit(mod(OP+remote+ranging,2)+1).name  % LTFB=odd OP=even
  % OP=1, remote=0 or OP=0, remote=1 => even ; OP=0, remote=0 or OP=1, remote=1 => odd
  nom=strrep(dirlist(dirnum).name,'.bin','.mat');
  if (ranging==1)
    nomout=['rangingclaudio',nom];
  else
    if (remote==1)
       nomout=['remote',nom];
    else
       nomout=['local',nom];
    end
  end
  nomoutgz=[nomout,'.gz'];
  if ((exist(nomout)==0)&&(exist(nomoutgz)==0))
    f=fopen([codelocation,'/',nomin]);
    code=fread(f,inf,'int8');
    code=repelems(code,[[1:length(code)] ; ones(1,length(code))*2]); % interpolate
    code=2*code-1;  % +1/-1
    fcode=fft(code');
    fclose(f);
    dirlist(dirnum).name
    eval(["f=fopen('",datalocation,"/",dirlist(dirnum).name,"');"]);
    d=fread(f,fs*2*10,'int16');
    p=1;
    pfreq=1;
    temps=[0:length(code)-1]'/fs;
    freq=linspace(-fs/2,fs/2-fs/fs,fs*ls);
    printf("n\tdt1\tdf1\tP1\tSNR1\tdt2\tdf2\tP2\tSNR2\r\n");
    if ((remote!=1)||(ranging==1))
       k=find((freq<5000)&(freq>-5000));
    else
       if (OP==1)
           k=find((freq>-12000)&(freq<12000)); % -50 kHz
       else
           k=find((freq<120000)&(freq>80000));
       end
    end
    dold=[];
    moved=[];
    movedval=[];
    do
      d=fread(f,fs*2*ls,'int16');         % ls s
      longueur=length(d);
      if (longueur==fs*2*ls)              % ls s
        d=d(1:2:end)+j*d(2:2:end);
%        if (remote==1)
%           d2=fftshift(abs(fft(d(remotechannel:2:end).^2))); % 0.5 Hz accuracy
%           d=[dold ; d(remotechannel:2:end)];
%        else
           d2=fftshift(abs(fft(d(1:end).^2))); % 0.5 Hz accuracy
           d=[dold ; d(1:end)];
%        end
        [~,df(pfreq)]=max(d2(k));df(pfreq)=df(pfreq)+k(1)-1;df(pfreq)=freq(df(pfreq))/2;df(pfreq)
        dindex=1;
        do
          dpart=d(round(dindex):round(dindex)+length(fcode)-1);dpart=dpart-mean(dpart);
          [xval1(p),indice1(p),correction1(p),SNR1r(p),SNR1i(p),puissance1(p),puissancecode,puissancenoise]=processing(dpart,k,df(pfreq));
          indice1(p)=floor(indice1(p)/(2*Nint+1));
          if (10*log10(SNR1i(p)+SNR1r(p))>-30)
             if (((indice1(p)>43)&&(indice1(p)<length(code)/2)) || ((indice1(p)<length(code)-2)&&(indice1(p)>length(code)/2)))
  printf("MOVED %d\n",indice1(p));
  moved=[moved p];
  movedval=[movedval indice1(p)+1];
                if ((dindex-indice1(p)+1)<0) 
                   dindex=dindex+length(fcode);
                end 
                dindex=dindex-(indice1(p))+21;
                dpart=d(round(dindex):round(dindex)+length(fcode)-1); dpart=dpart-mean(dpart); % measurement
                [xval1(p),indice1(p),correction1(p),SNR1r(p),SNR1i(p),puissance1(p),puissancecode,puissancenoise]=processing(dpart,k,df(pfreq));
             end
  % figure; plot(temps,conv(angle(y.*code'),ones(100,1)/100)(50:end-50),'.');
  % xlabel('time (s)');  ylabel('arg(code.*data) (s)')
          end
          printf("%d\t%.12f\t%.3f\t%.1f\t%.1f\r\n",p,(indice1(p)-1+correction1(p))/fs/(2*Nint+1),df(pfreq),10*log10(puissance1(p)),10*log10(SNR1i(p)+SNR1r(p)))
          p=p+1;
          dindex=dindex+length(fcode);
        until (dindex+length(fcode)-1>length(d))
      end
      if (exist('dindex'))
        if (dindex<length(d)) 
           dold=d(round(dindex):end);
        else dold=[];
        end
  %    if (length(dold)>0) length(dold)
  %       end
        pfreq=pfreq+1;
      end
    until (longueur!=fs*2*ls);  % ls s
    fclose(f)
    eval(['save -mat ',nomout,' corr* df indic* SNR* code puissan* xval* moved*']);
    clear corr* df* indic* p SNR* puissa* xval*
    ddir=dir(['*remote*',nom,'*']);
    if (isempty(ddir)==0)
        eval(['system(''mv ',datalocation,'/',dirlist(dirnum).name,' ',datalocation,'/donetw/'')']);
    end
  else
    printf("%s already done\n",nomout);
  end
end
