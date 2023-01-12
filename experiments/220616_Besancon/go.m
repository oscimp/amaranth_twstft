fs=5e6

x=load('SATREranging');
temps=x(:,1)*3600*24+x(:,2)*3600+x(:,3)*60+x(:,4);
temps1=temps(1);
%temps=temps-temps(1);
plot(temps+7200,x(:,5)/1e9,'r.')
hold on

initemps=0;
dirlist=dir('./*mat');
for dirnum=1:length(dirlist)
  eval(['load ',dirlist(dirnum).name]);
  filname=strrep(dirlist(dirnum).name,'.mat','');
  temps=localtime(str2num(filname));
  solution1=indice1+correction1;
  solution2=indice2+correction2;
  heure=(temps.mday*24+temps.hour)*ones(1,length(solution1));
  secon=[0:length(solution1)-1]+temps.min*60;
  temp=heure*3600+secon;
%  if (initemps==0)
%     initemps=temp(1);
%  end
  temp=temp-initemps;
  hold on
  s=(solution1-solution2)/fs;
  sk=find(s<0);
  if (isempty(sk)==0)
     s(sk)=1+s(sk);
  end
  plot(temp,s,'o'); % ranging solution
  mondf(dirnum)=mean(df);
%  sol2=(solution1-solution2)/fs;
%  xlabel('time (s)')
%  ylabel('ranging delay (s)')
end

figure
plot(mondf)

if (1==0)
subplot(212)
t=[temps']; % temp1 temp2];
s=[x(:,4)'/1e9];% sol1 sol2];
sdrt=[temp1 temp2];
sdrs=[sol1 sol2];
[a,b]=polyfit(t,s,2);
plot(t,s-b.yf,'x')
hold on
plot(sdrt,sdrs-polyval(a,sdrt),'b.')
xlabel('time (s)')
ylabel('residue (parabolic fit) (s)')
end
