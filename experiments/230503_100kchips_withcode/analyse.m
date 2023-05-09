close all
clear all
fs=5e6

dirlistanalyse=dir('OP/rang*mat.gz')
for dirnumanalyse=1:length(dirlistanalyse)
  eval(['load OP/',dirlistanalyse(dirnumanalyse).name])
  [a,b]=polyfit([60:length(indice1)]/25,unwrap((indice1+correction1)(60:end)*2*pi)/2/pi/3/fs,1);
  sol(dirnumanalyse)=a(1);
  temps(dirnumanalyse)=str2num(dirlistanalyse(dirnumanalyse).name(15:24));
  soldf(dirnumanalyse)=mean(df(60:end));
end
figure(1)
subplot(211)
plot(temps,sol,'x-');xlabel('time (s)'),ylabel('velocity (s/s)'); title('ranging')
hold on
subplot(212)
plot(temps,soldf,'x-');xlabel('time (s)'),ylabel('freq. offset (Hz)');
hold on
clear sol temps soldf

dirlistanalyse=dir('OP/remo*mat.gz')
for dirnumanalyse=1:length(dirlistanalyse)
  eval(['load OP/',dirlistanalyse(dirnumanalyse).name])
  [a,b]=polyfit([60:length(indice1)]/25,unwrap((indice1+correction1)(60:end)*2*pi)/2/pi/3/fs,1);
  sol(dirnumanalyse)=a(1);
  temps(dirnumanalyse)=str2num(dirlistanalyse(dirnumanalyse).name(14:23));
  soldf(dirnumanalyse)=mean(df(60:end));
end
figure(2)
subplot(211)
plot(temps,sol,'x-');xlabel('time (s)'),ylabel('velocity (s/s)'); title('one way')
hold on
subplot(212)
plot(temps,soldf,'x-');xlabel('time (s)'),ylabel('freq. offset (Hz)');
hold on
clear sol temps soldf

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
dirlistanalyse=dir('LTFB/rang*mat.gz')
for dirnumanalyse=1:length(dirlistanalyse)
  eval(['load LTFB/',dirlistanalyse(dirnumanalyse).name])
  [a,b]=polyfit([60:length(indice1)]/25,unwrap((indice1+correction1)(60:end)*2*pi)/2/pi/3/fs,1);
  sol(dirnumanalyse)=a(1);
  temps(dirnumanalyse)=str2num(dirlistanalyse(dirnumanalyse).name(15:24));
  soldf(dirnumanalyse)=mean(df(60:end));
end
figure(3)
subplot(211)
plot(temps,sol,'rx-');
subplot(212)
plot(temps,soldf,'rx-');xlabel('time (s)'),ylabel('freq. offset (Hz)');
clear sol temps soldf
legend('OP','LTFB')

dirlistanalyse=dir('LTFB/remo*mat.gz')
for dirnumanalyse=1:length(dirlistanalyse)
  eval(['load LTFB/',dirlistanalyse(dirnumanalyse).name])
  [a,b]=polyfit([60:length(indice1)-7]/25,unwrap((indice1+correction1)(60:end-7)*2*pi)/2/pi/3/fs,1);
  sol(dirnumanalyse)=a(1);
  temps(dirnumanalyse)=str2num(dirlistanalyse(dirnumanalyse).name(14:23));
  soldf(dirnumanalyse)=mean(df(60:end-7));
end
figure(2)
subplot(211)
plot(temps,sol,'rx-');
subplot(212)
plot(temps,soldf-1e5,'rx-');xlabel('time (s)'),ylabel('freq. offset (Hz)');
clear sol temps soldf
legend('OP','LTFB')

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
