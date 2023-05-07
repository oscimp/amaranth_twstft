close all
clear all
fs=5e6

dirlistanalyse=dir('rang*mat')
for dirnumanalyse=1:length(dirlistanalyse)
  eval(['load ',dirlistanalyse(dirnumanalyse).name])
  [a,b]=polyfit([60:length(indice1)]/25,unwrap((indice1+correction1)(60:end)*2*pi)/2/pi/3/fs,1);
  sol(dirnumanalyse)=a(1);
  temps(dirnumanalyse)=str2num(dirlistanalyse(dirnumanalyse).name(15:24));
  soldf(dirnumanalyse)=mean(df(60:end));
end
subplot(211)
plot(temps,sol,'x-');xlabel('time (s)'),ylabel('velocity (s/s)'); title('ranging')
subplot(212)
plot(temps,soldf,'x-');xlabel('time (s)'),ylabel('freq. offset (Hz)');

dirlistanalyse=dir('remo*mat')
for dirnumanalyse=1:length(dirlistanalyse)
  eval(['load ',dirlistanalyse(dirnumanalyse).name])
  [a,b]=polyfit([60:length(indice1)]/25,unwrap((indice1+correction1)(60:end)*2*pi)/2/pi/3/fs,1);
  sol(dirnumanalyse)=a(1);
  temps(dirnumanalyse)=str2num(dirlistanalyse(dirnumanalyse).name(14:23));
  soldf(dirnumanalyse)=mean(df(60:end));
end
figure
subplot(211)
plot(temps,sol,'x-');xlabel('time (s)'),ylabel('velocity (s/s)'); title('one way')
subplot(212)
plot(temps,soldf,'x-');xlabel('time (s)'),ylabel('freq. offset (Hz)');

dirlistanalyse=dir('loca*mat')
for dirnumanalyse=1:length(dirlistanalyse)
  eval(['load ',dirlistanalyse(dirnumanalyse).name])
  [a,b]=polyfit([60:length(indice1)]/25,unwrap((indice1+correction1)(60:end)*2*pi)/2/pi/3/fs,1);
  sol(dirnumanalyse)=a(1);
  temps(dirnumanalyse)=str2num(dirlistanalyse(dirnumanalyse).name(13:22));
  soldf(dirnumanalyse)=mean(df(60:end));
end
figure
subplot(211)
plot(temps,sol,'x-');xlabel('time (s)'),ylabel('velocity (s/s)'); title('loopback')
subplot(212)
plot(temps,soldf,'x-');xlabel('time (s)'),ylabel('freq. offset (Hz)');

return

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
