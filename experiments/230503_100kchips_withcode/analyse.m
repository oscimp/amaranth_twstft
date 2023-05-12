close all
clear all
fs=5e6

if (1==0)
dirlistanalyseOP=dir('OP/rang*mat.gz')
dirlistanalyseLTFB=dir('LTFB/local*mat.gz')
for dirnumanalyse=1:length(dirlistanalyseOP)
  eval(['load OP/',dirlistanalyseOP(dirnumanalyse).name])
  [aOP,b]=polyfit([60:length(indice1)]/25,unwrap((indice1+correction1)(60:end)*2*pi)/2/pi/3/fs,1);
  solOP(dirnumanalyse)=aOP(1);
  tempsOP(dirnumanalyse)=str2num(dirlistanalyseOP(dirnumanalyse).name(15:24));
  soldfOP(dirnumanalyse)=mean(df(60:end));
  eval(['load LTFB/',dirlistanalyseLTFB(dirnumanalyse).name])
  [aLTFB,b]=polyfit([60:length(indice1)]/25,unwrap((indice1+correction1)(60:end)*2*pi)/2/pi/3/fs,1);
  solLTFB(dirnumanalyse)=aLTFB(1);
  tempsLTFB(dirnumanalyse)=str2num(dirlistanalyseLTFB(dirnumanalyse).name(13:22));
  soldfLTFB(dirnumanalyse)=mean(df(60:end));
  r1(dirnumanalyse)=aLTFB(2)-aOP(2);
end
figure(1)
subplot(211)
plot(tempsOP,solOP,'x-');xlabel('time (s)'),ylabel('velocity (s/s)'); title('ranging')
hold on
plot(tempsLTFB,solLTFB,'rx-');
subplot(212)
plot(tempsOP,soldfOP,'x-');xlabel('time (s)'),ylabel('freq. offset (Hz)');
hold on
plot(tempsLTFB,soldfLTFB,'rx-');
legend('OP','LTFB')
clear solOP tempsOP soldfOP solLTFB tempsLTFB soldfLTFB
r1
end

deb=8;
dur=160;
dirlistanalyseOP=dir('OP/remo*mat.gz')
dirlistanalyseLTFB=dir('LTFB/remo*mat.gz')
for dirnumanalyse=14:25 % 1:length(dirlistanalyseOP)
  eval(['load OP/',dirlistanalyseOP(dirnumanalyse).name])
  k=find(indice1>100000);
  if (isempty(k)==0) indice1(k)=indice1(k)-200000;end
  [aOP,b]=polyfit([deb:1/25:deb+dur],unwrap((indice1+correction1)(deb*25:deb*25+dur*25)*2*pi)/2/pi/3/fs,1);
  solOP(dirnumanalyse)=aOP(1);
  tempsOP(dirnumanalyse)=str2num(dirlistanalyseOP(dirnumanalyse).name(14:23));
  soldfOP(dirnumanalyse)=mean(df(deb:deb+dur));
  delaiOP=unwrap((indice1+correction1)(deb*25:deb*25+dur*25)*2*pi)/2/pi/3/fs;
  eval(['load LTFB/',dirlistanalyseLTFB(dirnumanalyse).name])
  k=find(indice1>100000);
  if (isempty(k)==0) indice1(k)=indice1(k)-200000;end
  [aLTFB,b]=polyfit([deb:1/25:deb+dur],unwrap((indice1+correction1)(deb*25:deb*25+dur*25)*2*pi)/2/pi/3/fs,1);
  solLTFB(dirnumanalyse)=aLTFB(1);
  tempsLTFB(dirnumanalyse)=str2num(dirlistanalyseLTFB(dirnumanalyse).name(14:23));
  soldfLTFB(dirnumanalyse)=mean(df(deb:deb+dur));
  delaiLTFB=unwrap((indice1+correction1)(deb*25:deb*25+dur*25)*2*pi)/2/pi/3/fs;
  r2(dirnumanalyse)=aLTFB(2)-aOP(2);
subplot(211)
plot([0:length(delaiLTFB)-1]/25,0.5*(delaiOP-delaiLTFB-(delaiOP-delaiLTFB)(1)))
hold on
s(dirnumanalyse)=std(delaiOP-delaiLTFB);
m(dirnumanalyse)=mean(delaiOP-delaiLTFB);
end
xlabel('time (s)')
ylabel('TW delay (s)')
subplot(212)
plot(s)
xlabel('session index (h)')
ylabel('std delay (s)')

figure(2)
subplot(211)
plot(tempsOP,solOP,'x-');xlabel('time (s)'),ylabel('velocity (s/s)'); title('one way')
hold on
plot(tempsLTFB,solLTFB,'rx-');
subplot(212)
plot(tempsOP,soldfOP,'x-');xlabel('time (s)'),ylabel('freq. offset (Hz)');
hold on
plot(tempsLTFB,soldfLTFB,'rx-');
legend('OP','LTFB')
clear sol temps soldf
r2

return

dirlistanalyse=dir('OP/loca*mat.gz')
for dirnumanalyse=1:length(dirlistanalyse)
  eval(['load OP/',dirlistanalyse(dirnumanalyse).name])
  [a,b]=polyfit([60:length(indice1)]/25,unwrap((indice1+correction1)(60:end)*2*pi)/2/pi/3/fs,1);
  sol(dirnumanalyse)=a(1);
  temps(dirnumanalyse)=str2num(dirlistanalyse(dirnumanalyse).name(13:22));
  soldf(dirnumanalyse)=mean(df(60:end));
end
figure(3)
subplot(211)
plot(temps,sol,'x-');xlabel('time (s)'),ylabel('velocity (s/s)'); title('loopback')
hold on
subplot(212)
plot(temps,soldf,'x-');xlabel('time (s)'),ylabel('freq. offset (Hz)');
hold on
clear sol temps soldf

%%%%%%%%%%%%%%%%%

dirlistanalyse=dir('LTFB/loca*mat.gz')
for dirnumanalyse=1:length(dirlistanalyse)
  eval(['load LTFB/',dirlistanalyse(dirnumanalyse).name])
  [a,b]=polyfit([60:length(indice1)]/25,unwrap((indice1+correction1)(60:end)*2*pi)/2/pi/3/fs,1);
  sol(dirnumanalyse)=a(1);
  temps(dirnumanalyse)=str2num(dirlistanalyse(dirnumanalyse).name(13:22));
  soldf(dirnumanalyse)=mean(df(60:end));
end
figure(1)
subplot(211)
plot(temps,sol,'rx-');
subplot(212)
plot(temps,soldf,'rx-');xlabel('time (s)'),ylabel('freq. offset (Hz)');
clear sol temps soldf
legend('OP','LTFB')
return
figure
plot(ltfbr-ltfbl-(opr-opl))

load localclaudio1681909561.1681909746.60053.mat
x=(angle(xval1)-angle(xval1.^2)/2);
k=find(x<-1);
x(k)=x(k)+2*pi;
plot(x,'-')
x=(angle(xval1)-angle(xval1.^2)/2);
hold on
plot(x,'r-')
title('local')

load remoteclaudio1681909561.1681909746.60053.mat
x=(angle(xval1)-angle(xval1.^2)/2);
figure
plot(x,'-');hold on
k=find(x<-1);
x(k)=x(k)+2*pi;
plot(x,'-')
title('remote')
[a,b]=polyfit([60:length(indice1)]/25,unwrap((indice1(60:end)+correction1(60:end))*2*pi)/2/pi/fs/3*1e9,1)
std(conv(unwrap((indice1(60:end)+correction1(60:end))*2*pi)/2/pi/fs/3*1e9-b.yf,ones(25,1)/25)(25:end-25))

figure
plot(conv(unwrap((indice1(60:end)+correction1(60:end))*2*pi)/2/pi/fs/3*1e9-b.yf,ones(25,1)/25)(25:end-25))
[a,b]=polyfit([60:length(indice1)]/25,unwrap((indice1(60:end)+correction1(60:end))*2*pi)/2/pi/fs/3*1e9,2)
hold on
plot(conv(unwrap((indice1(60:end)+correction1(60:end))*2*pi)/2/pi/fs/3*1e9-b.yf,ones(25,1)/25)(25:end-25))
std(conv(unwrap((indice1(60:end)+correction1(60:end))*2*pi)/2/pi/fs/3*1e9-b.yf,ones(25,1)/25)(25:end-25))
