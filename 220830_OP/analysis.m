clear all
pkg load signal

% selection for analyzing SDR (Zynq), OP SATRE or UME SATRE
dirlistana=dir('./*SDR*.mat');satre=0;
% dirlistana=dir('./*OP*.mat');satre=0+1;
% dirlistana=dir('./*UME*.mat');satre=19+1;

function myarray=analyse_satre(x,satre,ye0,mo0,da0,ho0,mi0,se0,df)
  [a,b]=polyfit([1:length(x)],x,2);
  x=x-b.yf;
  k=find(abs(x)>10e-9);
  if (isempty(k)==0)
    if (k(1)==1) k=k(2:end);end
    if (k(end)==length(x)) k=k(1:end-1);end
    x(k)=NaN;
    x(k-1)=NaN;
    x(k+1)=NaN;
  end
  k=find(isnan(x)==0);
  x=x(k);
  df=df(k);
  if (satre!=0)
     x=conv(x,ones(250,1)/250)(125:end-125);
     x=x(1:250:end);
     df=df(1:250:end);
  end
  s=std(x)
  y=ye0*ones(1,length(x));
  mo=mo0*ones(1,length(x));
  d=da0*ones(1,length(x));
  h=ho0*ones(1,length(x));
  mi=mi0*ones(1,length(x));
  s=se0*ones(1,length(x));
  mx=x;
  sx=zeros(1,length(x));
  p=zeros(1,length(x));
  snr=zeros(1,length(x));
  myarray=[y; mo; d; h; mi; s; df; mx ;sx; p; snr]';
end

for dirnumana=1:length(dirlistana)
  eval(['load ',dirlistana(dirnumana).name]);
  dirlistana(dirnumana).name
  if isempty(strfind(dirlistana(dirnumana).name,'UME'))
     if isempty(strfind(dirlistana(dirnumana).name,'SDR'))
        k=find(abs(xval1)>mean(abs(xval1(1:250)))*5); % 1st second
     else
        if (isempty(strfind(dirlistana(dirnumana).name,'17h05'))==0)
          xval1=xval1(1:550);     % remove second part after TX stopped
          indice1=indice1(1:550);
          indice2=indice2(1:550);
          correction1_a=correction1_a(1:550);
          correction2_a=correction2_a(1:550);
          df=df(1:550);
        end
        if (isempty(strfind(dirlistana(dirnumana).name,'15h05'))==0)
          xval1=xval1(1:700);     % remove second part after TX stopped
          indice1=indice1(1:700);
          indice2=indice2(1:700);
          correction1_a=correction1_a(1:700);
          correction2_a=correction2_a(1:700);
          df=df(1:700);
        end
        if (isempty(strfind(dirlistana(dirnumana).name,'11h00'))==0)
          xval1=xval1([1 545:end]);     % remove second part after TX stopped
          indice1=indice1([1 545:end]);
          indice2=indice2([1 545:end]);
          correction1_a=correction1_a([1 545:end]);
          correction2_a=correction2_a([1 545:end]);
          df=df([1 545:end]);
          xval1(1)=xval2(2);
        end
        if (isempty(strfind(dirlistana(dirnumana).name,'11h30'))==0)
          xval1=xval1([2:300]);     % remove second part after TX stopped
          indice1=indice1([2:300]);
          indice2=indice2([2:300]);
          correction1_a=correction1_a([2:300]);
          correction2_a=correction2_a([2:300]);
          df=df([2:300]);
        end
        k=find(abs(xval1)>mean(abs(xval1(1))*5));     % 5 first seconds
     end
  else 
     if (isempty(strfind(dirlistana(dirnumana).name,'11h00'))==0) 
        xval1=xval1(20710:end);     % X310 lost samples UUUDDD
        indice1=indice1(20710:end);
        correction1_a=correction1_a(20710:end);
        df=df(20710:end);
     end
     k=find(abs(indice1-mean(indice1))<100);          % UME continuous stream
  end
%  solution1=(indice1(k)+correction1_1(k))/fs/(Nint*2+1); analyse_satre(solution1,1);
%  solution2=(indice1(k)+correction1_2(k))/fs/(Nint*2+1); analyse_satre(solution2,1);
%  solution3=(indice1(k)+correction1_3(k))/fs/(Nint*2+1); analyse_satre(solution3,1);
% identify hour min from filename
  h0=str2num(dirlistana(dirnumana).name(1:2));
  if (isempty(h0)) h0=str2num(dirlistana(dirnumana).name(4:5));end
  m0=str2num(dirlistana(dirnumana).name(4:5));
  if (isempty(m0)) m0=str2num(dirlistana(dirnumana).name(7:8));end
  s0=0;
  solutiona=(indice1(k)+correction1_a(k))/fs/(Nint*2+1); 
  df=df(k);
  myarray=analyse_satre(solutiona,satre,2022,08,30,h0,m0,s0,df);
  if (isempty(strfind(dirlistana(dirnumana).name,'SDR'))==0) % SDR: we have both channels
    solution2a=(indice2(k)+correction2_a(k))/fs/(Nint*2+1); 
    myarray=analyse_satre(solutiona-solution2a,satre,2022,08,30,h0,m0,s0,df);
    save -text myarray.txt myarray
  end
  subplot(length(dirlistana),1,dirnumana)
  plot(myarray(:,8))
  xlabel('time (s)');ylabel('delay (s)');legend(strrep(dirlistana(dirnumana).name,'.mat',''))
end

% Summary of results (impact of emission power)
%               SATRE OP   SATRE UME  Zedboard     Measurement conditions
% 15h05OP.mat = 1.5540e-10 4.9125e-10 3.6381e-10   SATRE
% 15h30OP.mat = 1.8580e-10 4.0207e-10 2.7078e-10   SATRE      Zed+3 dB
% 17h05OP.mat = 2.6289e-10 9.1155e-10 2.4009e-10   SATRE+3 dB Zed+3 dB
% j2 1100          NA      5.3416e-10   ?????      NoSATRE    Zed   SATRE X310_diff
% j2 1130          NA      5.3234e-10 2.7440e-10   NoSATRE    Zed+3 SATRE X310_diff+3
% j2 1305          NA      3.0283e-10 2.8107e-10   NoSATRE    X310_same_TX/RX

%interpolation factor impact (>0 is mandatory, >1 is not useful)
%15h30UMEinterp0.mat    6.1225e-09  <- no interpolation = fluctuations
%15h30UMEinterp1.mat    4.0207e-10
%15h30UMEinterp2.mat    4.5542e-10
%17h05UMEinterp0.mat    6.1905e-09  <- no interpolation = fluctuations
%j2-13h05UMEinterp0.mat 6.1043e-09  <- no interpolation = fluctuations
%j2-13h05UMEinterp1.mat 3.3635e-10 after decimation, 3.3419e-10 before decimation 1:250:end

%                    single chan ref-meas diff
% 17h05SDRinterp1.mat 2.5713e-10 2.5554e-10
% 17h05SDRinterp2.mat 2.4164e-10 2.4009e-10
