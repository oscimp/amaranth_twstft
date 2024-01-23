graphics_toolkit('gnuplot')
clear all
close all
format long
gr=0

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

dirlistrem=dir('./2401_LTFB/rem*mat.gz');
dirlistloc=dir('./2401_LTFB/loc*mat.gz');

for dirnum=1:length(dirlistrem)
  dirlistrem(dirnum).name
  eval(['load 2401_LTFB/',dirlistrem(dirnum).name]);
  r=(indice1+correction1/3);
  k=find(abs(xval1>max(abs(xval1)/2)));
  r=r(k(1):k(end));
  snrltfb(dirnum)=max((SNR1r+j*SNR1i)(k));
  m=find(moved>5 & moved<500);
  if (isempty(m)==0)
%     printf("r:")
     mr=movedval(m);
  end
  mfin=find(moved>1000 & moved<7500);
  if (isempty(mfin)==0)
    mfinr=moved(mfin(1))-moved(m(1))-1;
    printf("mfinr = %f\n",mfinr)
  end
  dfltfb(dirnum)=mean(df(30:end-30));
  tmp=str2num(dirlistrem(dirnum).name(14:23));
  tmp=datevec(tmp/86400+datenum('1/1/1970','mm/dd/yyyy'));
  tmp=julianDay(tmp(1),tmp(2),tmp(3)+(tmp(4)+tmp(5)/60+tmp(6)/3600)/24)-2400000.5-60000;
  thedateltfb(dirnum)=tmp;
  rslope=r(70:end)*Ts;
  kslope=find(abs(rslope-mean(rslope)<1000));
  rslope=rslope(kslope);
  [u,v]=polyfit([1:length(rslope)]*Tc,rslope,2);
  slopeltfb(dirnum)=u(2);
  stdltfb(dirnum)=std(conv(rslope-v.yf,ones(25,1)/25)(25:end-25));
  if ((length(k)==4500) || (length(k)>=7385))
     
% loopback LTFB
     eval(['load 2401_LTFB/',dirlistloc(dirnum).name]);
     l=(indice1+correction1/3);
     k=find(abs(xval1>max(abs(xval1)/2)));
     l=l(k(1):k(end));
     m=find(moved>50 & moved<500);
     if (isempty(m)==0)
        ml=movedval(m);
     end

% loopback OP
     dirlistOPloc=dir(['./2401_OP/lo*',dirlistloc(dirnum).name(13:21),'*gz']);
     if (isempty(dirlistOPloc)==0)
       eval(['load ./2401_OP/',dirlistOPloc.name]);
       lop=(indice1+correction1/3);
       k=find(abs(xval1>max(abs(xval1)/2)));
       lop=lop(k(1):k(end));
       m=find(moved>50 & moved<500);
       if (isempty(m)==0)
  %        printf("lop:")
          mlop=movedval(m);
       end
  % remote OP
       dirlistOPrem=dir(['./2401_OP/re*',dirlistloc(dirnum).name(13:21),'*gz']);
       if (isempty(dirlistOPrem)==0)
         eval(['load ./2401_OP/',dirlistOPrem.name]);
         tmp=str2num(dirlistOPrem.name(14:23));
         tmp=datevec(tmp/86400+datenum('1/1/1970','mm/dd/yyyy'));
         tmp=julianDay(tmp(1),tmp(2),tmp(3)+(tmp(4)+tmp(5)/60+tmp(6)/3600)/24)-2400000.5-60000;
         thedateop(dirnum)=tmp;
         rop=(indice1+correction1/3);
         k=find(abs(xval1>max(abs(xval1)/2)));
         rop=rop(k(1):k(end));
         snrop(dirnum)=max((SNR1r+j*SNR1i)(k));
         m=find(moved>50 & moved<500);
         if (isempty(m)==0)
    %        printf("rop:")
            mrop=movedval(m);
         end
         mfin=find(moved>1000 & moved<7500);
         if (isempty(mfin)==0)
            mfino=moved(mfin(1))-moved(m(1))-1;
            printf("mfino = %f\n",mfino)
         end
         dfop(dirnum)=mean(df(30:end-30));
    % plot if wanted (many windows !)
         if (gr==1)
           figure
           subplot(311)
           plot(rop);hold on
           plot(r);hold on
           subplot(312)
           plot(lop);hold on
           plot(l);hold on
           subplot(313)
         end
    % check that all vectors are the same size, otherwise truncate
         minlength=length(r);
         if (length(rop)<minlength) minlength=length(rop);end
         if (length(l)<minlength) minlength=length(l);end
         if (length(lop)<minlength) minlength=length(lop);end
         r=r(1:minlength);
         l=l(1:minlength);
         lop=lop(1:minlength);
         rop=rop(1:minlength);
    % convert index to time (200 ns/period @ 5 MS/s)
         % res=0.5*((rop+mrop)-(lop+mlop)-((r+mr)-(l+ml)))*Ts;  % 0.5*(remote-local difference)
         res=0.5*((rop)-(lop)-((r)-(l)))*Ts;  % 0.5*(remote-local difference)
    
         if ((exist('mfino')==1) && (length(res)>mfino))
            res=res(1:mfino);
            r=r(1:mfino);
            rop=rop(1:mfino);
            clear mfino; 
            % figure;plot(res);title(['mfino ',strrep(dirlistOPrem(dirnum).name,'_',' ')])
         else
            if ((exist('mfinr')==1) && (length(res)>mfinr))
               res=res(1:mfinr);
               r=r(1:mfinr);
               rop=rop(1:mfinr);
               clear mfinr; 
               % figure;plot(res);title(['mfinr ',strrep(dirlistOPrem(dirnum).name,'_',' ')])
            end
         end
         
         printf("std loopback: OP=%f LTFB=%f\n",std(lop(70:end-10))*Ts, std(l(70:end-10))*Ts); % standard-deviation of loopback
    % remove outliers (erroneous frequency offset identification ?)
         res1s=reshape(res(1:floor(length(res)/25)*25),25,floor(length(res)/25));
         res1s=mean(res1s);
         k1s=find(abs(res1s-mean(res1s))<3*std(res1s));
         res1s=res1s(k1s);
         if (mean(res1s(70:end))<0) res1s=res1s+Ts/2; end
         if (mean(res1s(70:end))>Ts/2) res1s=res1s-Ts/2; end
         
         k=find(abs((res))<1000);res=res(k);
    % remove 1-sample error (200 ns/2 = 100 ns)
         if (mean(res(70:end))<0) res=res+Ts/2; end
         if (mean(res(70:end))>Ts/2) res=res-Ts/2; end
         if (gr==1)
           printf("OP: %f \t",(mrop-mlop)*Ts);
           printf("LTFB: %f diff: %f",(mr-ml)*Ts,((mrop-mlop)-((mr-ml)))*Ts);
           plot(res(70:end))
         end
         printf("mean: %.3f std: %.3f\n",mean(res(70:end)),std(conv(res(70:end),(ones(25,1)/25))(25:end-25)))
         
         rop=rop(70:end)*Ts;
         k=find(abs(rop-mean(rop)<1000));
         rop=rop(k);
         [u,v]=polyfit([1:length(rop)]*Tc,rop,2);
         slopeop(dirnum)=u(2);
         stdop(dirnum)=std(conv(rop-v.yf,ones(25,1)/25)(25:end-25));
    % results
         date1=str2num(dirlistrem(dirnum).name(14:23));
         date2=str2num(dirlistloc(dirnum).name(13:22));
         date3=str2num(dirlistOPloc.name(13:22));
         date4=str2num(dirlistOPrem.name(14:23));
    
         if ((abs(date1-date2)>1) || (abs(date1-date3)>1) || (abs(date1-date4)>1))
            printf("ERROR\n");
            thend
         else
            tmp=datevec(date1/86400+datenum('1/1/1970','mm/dd/yyyy'));
            thedate(dirnum)=julianDay(tmp(1),tmp(2),tmp(3)+(tmp(4)+tmp(5)/60+tmp(6)/3600)/24)-2400000.5-60000;
         end
    % output 1-s result
         
         final1s=[60000+thedate(dirnum)+k1s(70:end)/3600/24-1 ; res1s(70:end)]';  % removove first errouneous code
         outnom=strrep(strrep(dirlistrem(dirnum).name,'mat.gz','1s'),'remoteclaudio','')
         eval(['save -text ',outnom,' final1s']);
    % mean result:
         mres(dirnum)=mean(res(70:end));   % mean (should be parabolic fit !)
         sres(dirnum)=std(conv(res(70:end),ones(1,25)/25)(25:end-25));    % standard deviation
         dlen(dirnum)=length(res(70:end)); % number of samples involved in the statistics

if (sres(dirnum)>10)  % ?!
% localclaudio1704555941_1704556276.112874879.mat.gz
% remoteclaudio1704555941_1704556276.112874879.mat.gz
   k=find(res>(Ts/2));
   res(k)=res(k)-Ts/2;
   mres(dirnum)=mean(res(70:end));   % mean (should be parabolic fit !)
   sres(dirnum)=std(conv(res(70:end),ones(1,25)/25)(25:end-25));    % standard deviation
   dlen(dirnum)=length(res(70:end)); % number of samples involved in the statistics
   printf(" ** CORRECTING ?! %.3f %.3f\n",mres(dirnum),sres(dirnum));
end

       else
         printf("** NG: %s no remote OP\n",dirlistrem(dirnum).name);
       end
    else
       printf("** NG: %s no local OP\n",dirlistrem(dirnum).name);
    end
  else
     printf("** NG: %s too short: length(k)=%d\n",dirlistrem(dirnum).name,length(k));
  end
end
k=find(thedateop==0);thedateop(k)=NaN;
k=find(thedateltfb==0);thedateltfb(k)=NaN;
k=find(mres==0); mres(k)=NaN;thedate(k)=NaN;
k=find(stdltfb>5); stdltfb(k)=NaN; slopeltfb(k)=NaN;
k=find(stdop>5); stdop(k)=NaN;slopeop(k)=NaN;

res=[thedate ; mres]'
save -text res res

subplot(411)
errorbar(thedate,mres,sres)
axis tight
%xlabel('MJD-59000 (day)')
ylabel('TW delay (ns)')
ylim([mres(1)-2.5 mres(1)+3])
subplot(412)
plot(thedate,stdltfb,'.-');hold on
plot(thedate,stdop,'.-');
plot(thedate,sres,'.-');
axis tight
ylim([0 2])
%xlabel('MJD-59000 (day)')
ylabel('drms (ns)')
legend('LTFB','OP','TW','location','northwest')
subplot(413)
plot(thedateltfb,slopeltfb,'.');hold on
plot(thedateop,slopeop,'.');
%xlabel('MJD-59000 (day)')
ylabel('slope (ns/s)')
legend('LTFB','OP','location','southwest')
axis tight
ylim([-5 5])
subplot(414)
plot(thedateltfb,dfltfb-dfltfb(1),'.');hold on
plot(thedateop,dfop-dfop(1),'.');hold on
xlabel('MJD-60000 (day)')
ylabel('sat. freq.\ntranslation (Hz)')
legend('LTFB','OP','location','southwest')
axis tight
ylim([-200 200])

figure
subplot(211)
plot(thedateop,10*log10(abs(snrop)),'.');hold on
plot(thedateltfb,10*log10(abs(snrltfb)),'.');hold on
line([thedateop(1) thedateop(end)],[10*log10(mean(abs(snrop))) 10*log10(mean(abs(snrop)))],'color','blue')
line([thedateltfb(1) thedateop(end)],[10*log10(mean(abs(snrltfb))) 10*log10(mean(abs(snrltfb)))],'color','red')
legend('OP','LTFB','location','southwest')
xlabel('time MJD-60000 (days)')
ylabel('SNR (dB)')
axis tight
ylim([-16 -11])
10*log10(mean(abs(snrop)))
10*log10(mean(abs(snrltfb)))
