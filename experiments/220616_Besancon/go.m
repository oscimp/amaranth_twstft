fs=5e6

% https://kotetsu1701.com/blog/programing-language-octave/
% Julian Day
function julian = julianDay(year, month, day)
    branch = year + (month - 1.0) / 12.0 + day / 365.25;

    if (floor(month) < 3)
        month = month + 12.0;
        year = year - 1.0;
    endif

    if (branch >= 1582.78)
        julian = floor(year * 365.25) + floor(year / 400.0) - floor(year / 100.0) + floor(30.59 * (month - 2.0)) + day + 1721088.5;
    elseif (branch >= 0.0)
        julian = floor(year * 365.25) + floor(30.59 * (month - 2.0)) + day + 1721086.5;
    elseif (year < 0.0)
        julian = sign(year) * floor(abs(year) * 365.25) + floor(30.59 * (month - 2.0)) + day + 1721085.5;
    end
end

subplot(211)
x=load('SATREranging');
temps=julianDay(2022,6,x(:,1)+x(:,2)/24+x(:,3)/24/60+x(:,4)/24/60/60);
temps1=temps(1);
%temps=temps-temps(1);
plot(temps(1:60:end)-2400000.5-59000,x(1:60:end,5)/1e9,'r.')
hold on

dirlist=dir('./*mat.gz');
for dirnum=1:length(dirlist)
  eval(['load ',dirlist(dirnum).name]);
  filname=strrep(dirlist(dirnum).name,'.mat.gz','');
  temps=str2num(filname)/86400+40587-59000;
  solution1=indice1+correction1;
  solution2=indice2+correction2;
%  if (initemps==0)
%     initemps=temp(1);
%  end
  hold on
  s=(solution1-solution2)/fs;
  sk=find(s<0);
  if (isempty(sk)==0)
     s(sk)=1+s(sk);
  end
  plot(temps,mean(s),'o'); % ranging solution
  mondf(dirnum)=mean(df);
  mont(dirnum)=temps(1);
%  sol2=(solution1-solution2)/fs;
%  xlabel('time (s)')
%  ylabel('ranging delay (s)')
end
ylim([.26285 .263])
ylabel('ranging delay (s)')
xlabel('MJD-59000 (day)')
return

figure
plot((mont-mont(1))/3600,mondf)

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
