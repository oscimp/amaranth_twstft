graphics_toolkit('gnuplot')
clear all
close all
format long
gr=0
% dirpos=['./2401_OP/']
dirpos=['./2401_LTFB/']

Ts=200;   % sampling period (ns) 
Tc=40e-3; % code period (s) 

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

dirlistloc=dir([dirpos,'loc*mat.gz']);
dirlistran=dir([dirpos,'ran*mat.gz']);

for dirnum=1:length(dirlistran)
  dirlistran(dirnum).name
  eval(['load ',dirpos,dirlistran(dirnum).name]);
  r=(indice1+correction1/3);
  k=find(abs(xval1>max(abs(xval1)/2)));
  r=r(k(1):k(end));
  m=find(moved>5 & moved<500);
  if (isempty(m)==0)
%     printf("r:")
     mr=movedval(m(1));
  end
  mfin=find(moved>1000 & moved<7500);
  if (isempty(mfin)==0)
    mfinr=moved(mfin(1))-moved(m(1))-1;
    printf("mfinr = %f\n",mfinr)
  end
  if ((length(k)==4500) || (length(k)>=7485))
     
% loopback LTFB
     eval(['load ',dirpos,dirlistloc(dirnum).name]);
     l=(indice1+correction1/3);
     k=find(abs(xval1>max(abs(xval1)/2)));
     l=l(k(1):k(end));
     m=find(moved>50 & moved<500);
     if (isempty(m)==0)
        ml=movedval(m(1));
     end

    % check that all vectors are the same size, otherwise truncate
     minlength=length(r);
     if (length(l)<minlength) minlength=length(l);end
     r=r(1:minlength);
     l=l(1:minlength);
    % convert index to time (200 ns/period @ 5 MS/s)
     res=((r+mr)-(l+ml))*Ts;  % 0.5*(remote-local)
    
     if ((exist('mfinr')==1) && (length(res)>mfinr))
       res=res(1:mfinr);
       r=r(1:mfinr);
       clear mfinr; 
     end
    % remove 1-sample error (200 ns/2 = 100 ns)
     printf("l=%.3f r=%.3f mean=%.3f std: %.3f\n",mean(l(70:end)),mean(r(70:end)),mean(res(70:end)),std(conv(res(70:end),(ones(25,1)/25))(25:end-25)))
         
     r=r(70:end)*Ts;
     [u,v]=polyfit([1:length(r)]*Tc,r,2);
     slope(dirnum)=u(2);
     stdltfb(dirnum)=std(conv(r-v.yf,ones(25,1)/25)(25:end-25));
    % results
     date1=str2num(dirlistloc(dirnum).name(13:22));
    
     tmp=datevec(date1/86400+datenum('1/1/1970','mm/dd/yyyy'));
     thedate(dirnum)=julianDay(tmp(1),tmp(2),tmp(3)+(tmp(4)+tmp(5)/60+tmp(6)/3600)/24)-2400000.5-59000;
     mres(dirnum)=mean(res(70:end));   % mean (should be parabolic fit !)
     sres(dirnum)=std(conv(res(70:end),ones(1,25)/25)(25:end-25));    % standard deviation
     dlen(dirnum)=length(res(70:end)); % number of samples involved in the statistics
  else
     printf(" ** NG\n");
  end
end
k=find(thedate==0);thedate(k)=NaN;mres(k)=NaN;sres(k)=NaN;dlen(k)=NaN;
subplot(211)
plot(thedate,mres*1e-3,'x')
xlabel('date (MJD-59000, days)')
ylabel('ranging mod. 40 ms (us)')
legend('LTFB','location','northwest')
subplot(212)
plot(thedate,slope)
xlabel('date (MJD-59000, days)')
ylabel('velocity (ns/s)')
