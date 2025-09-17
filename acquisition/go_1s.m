dl=dir('OP/lo*gz');
for m=1:length(dl)
  if strfind(dl(m).name,"io17489")
     printf("%d\n",m)
     debut=m;
     break
  end
end

fs=5e6;
N=1;
affiche=0
gen_1s=1;

% https://kotetsu1701.com/blog/programing-language-octave/
pkg load nan

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

% JulianToDate
function [year, month, day] = julianToDate(julian)
    T = [31 28 31 30 31 30 31 31 30 31 30 31];

    jj = julian - 2400000.5;
    year = floor(0.0027379093 * (julian - 2400000.5) + 1858.877);
    month = 1.0;
    day = 0.0;

    julian = julianDay(year, month, day);

    r2 = jj - (julian - 2400000.5);
    if (mod(year, 4.0) == 0 && mod(year, 100.0) ~= 0 || mod(year, 400.0) == 0)
        T(1, 2) = 29
    endif

    r1 = 0.0;
    m = 1;
    while (m < 13)
        if (floor(r2) - r1 - T(1, m) <= 0)
            break;
        endif
        r1 = r1 + T(1, m);
        m = m + 1;
    endwhile

    month = m;
    day = r2 - r1;
    T(1, 2) = 28;

    if (month == 13)
        year = year + 1.0;
        month = month - 12.0;
    endif
end


p=1;
for ll=debut:length(dl) 
% for ll=length(dl)-150:length(dl) 
  dl(ll).name
  clear xval1 indice1 correction1
  eval(['load OP/',dl(ll).name]);
  if exist('xval1')
    k=find(abs(xval1)>max(abs(xval1))/2);
    kk=find(diff(k)>1);
    if (isempty(kk)==0)
       k=k(11:kk(1));
       printf(" *** truncated *** ")
    else
       k=k(11:end-1); % 25 ms/code => remove first 275 ms
    end
    oplo=indice1(k)+correction1(k)/(2*N+1);
    loplo(p)=length(oplo);
    oplo=oplo/fs*1e9;
    xval1oplo=xval1(k);
  
    % sample loss at OP loopback
    kk=find(abs(diff(oplo))>2);  % 2 ns jump in loopback !
    if (isempty(kk)==0)
       kk=kk(1);
       printf("Sample loss at %d\n",kk);
       if (kk>1)
          oplo=oplo(1:kk-1);
       end
    end
    if (length(oplo)>102)
      nom=strrep(strrep(dl(ll).name,'local','remote'),'_2','_1');
      if (exist(['OP/',nom])==2)
        clear xval1 indice1 correction1
        eval(['load OP/',nom]);
        xval1=xval1(k);
  
    kkk=find(abs(xval1)>max(abs(xval1))/2);
    kkkk=find(diff(kkk)>1);
    if (isempty(kkkk)==0)
       ll
       k=k(1:kkkk(1));
       printf(" *** truncated *** ")
       if kkkk(1)<length(oplo)
          oplo=oplo(1:kkkk(1));
       end
    end
  
        opre=indice1(k)+correction1(k)/(2*N+1);
        lopre(p)=length(opre);
        opre=opre/fs*1e9;
        opre=opre(1:length(oplo));
        snrop(p)=median(10*log10(abs(SNR1r(k)+SNR1i(k))*fs));
      
        nom=dir(['LTFB/',dl(ll).name(1:21),'*']);
        if (isempty(nom))
           printf("%s not found in LTFB\n",dl(ll).name(1:21));
        else
           nom=nom.name;
           tmp=str2num(nom(13:22));
           tmp=datevec(tmp/86400+datenum('1/1/1970','mm/dd/yyyy'));
           tmp=julianDay(tmp(1),tmp(2),tmp(3)+(tmp(4)+tmp(5)/60+tmp(6)/3600)/24)-2400000.5+0.5-8.4e-2; % JMF +0.5
           ladate(p)=tmp;
           printf("%s -> %s ",strrep(dl(ll).name,'localclaudio',''),strrep(nom,'localclaudio',''));
           clear xval1 indice1 correction1
           eval(['load LTFB/',nom]);
           if (exist('xval1'))
             k=find(abs(xval1)>max(abs(xval1))/2);
             kk=find(diff(k)>1);
             if (isempty(kk)==0)
                k=k(11:kk(1))
                printf(" *** truncated *** ")
             else
                k=k(11:end-1); % 25 ms/code => remove first 275 ms
             end
             ltlo=indice1(k)+correction1(k)/(2*N+1);
             lltlo(p)=length(ltlo);
             ltlo=ltlo/fs*1e9;
             xval1ltlo=xval1(k);
      
             nomre=strrep(strrep(nom,'local','remote'),'_1.','_2.');
             nomre=dir(['LTFB/',nomre(1:22),'*']);
             if length(nomre)>0
               nomre=nomre.name;
               clear xval1 indice1 correction1
               eval(['load LTFB/',nomre]);
               xval1=xval1(k);
      kkk=find(abs(xval1)>max(abs(xval1))/2);
      kkkk=find(diff(kkk)>1);
      if (isempty(kkkk)==0)
         k=k(1:kkkk(1));
         printf(" *** truncated *** ")
         ltlo=ltlo(1:kkkk(1));
      end
      if (length(kkk)<length(ltlo))
         k=k(1:kkk(end));
         ltlo=ltlo(1:kkk(end));
         printf(" *** truncated2 *** ")
      end
               ltre=indice1(k)+correction1(k)/(2*N+1);
               lltre(p)=length(ltre);
               ltre=ltre/fs*1e9;
               snrlt(p)=median(10*log10(abs(SNR1r(k)+SNR1i(k))*fs));
               printf("%d %d %d %d\n",loplo(p),lopre(p),lltlo(p),lltre(p));
               if (length(oplo)>length(ltlo))
                  oplo=oplo(1:length(ltlo));
                  opre=opre(1:length(ltlo));
               else
                  ltlo=ltlo(1:length(oplo));
                  ltre=ltre(1:length(oplo));
               end
               if ((length(opre)>2) && (length(ltre)>2))
                  [~,opre2]=polyfit([1:length(opre)],opre,2);
                  [~,ltre2]=polyfit([1:length(opre)],ltre,2);
                  res2=0.5*((opre2.yf-oplo)-(ltre2.yf-ltlo));
                  k=find(abs(res2-median(res2))>5);  % remove outliers
                  res2(k)=NaN;
                  % res2=mod(res2,200/(2*N+1)/2);
               end
        
                 res=0.5*((opre-oplo)-(ltre-ltlo));
                 k=find(abs(res-median(res))>5);  % remove outliers
                 res(k)=NaN;
    if std(res)>10
    ll
      figure
     subplot(221)
     plot([0:length(res)-1]/25,res);xlabel('time (s)');ylabel('TWSTFT (ns)');title(strrep(nom,'_',' '))
     subplot(222);plot(ltlo);hold on;plot(oplo)
     subplot(223);plot(ltre);
     subplot(224);plot(opre);
    end
    % eval(['print -dpdfcrop ',dl(ll).name,'.pdf'])
    % pause
    % close all
               % res=mod(res,200/(2*N+1)/2);
               ki=find(res>median(res)+10);
               res(ki)=res(ki)-200/(2*N+1);
               ki=find(res>median(res)-10);
               res(ki)=res(ki)+200/(2*N+1);
        if (1==0)
               if mean(res)<-10
                  res=res+200/(2*N+1)/2;
               end
               if mean(res)>20
                  res=res-200/(2*N+1)/2;
               end
               if mean(res2)<-10
                  res2=res2+200/(2*N+1)/2;
               end
               if mean(res)>20
                  res2=res2-200/(2*N+1)/2;
               end
        end
               if (affiche==1)
                 figure
                 subplot(313);
                 plot([0:length(res)-1]/25,res-res(1))
                 xlabel('time (s)')
                 ylabel('TW delay (ns)')
                 hold on
               end
               resmean(p)=mean(res);
      ng=find(abs(res-resmean(p))>3); % any value larger than 3 ns
  if (isempty(ng)!=0)
    printf("PROBLEM NG SAMPLES:");ng
  end
               resstd(p)=std(res);
               resmean2(p)=mean(res2);
               resstd2(p)=std(res2);
               if (std(res)>20)
                 if (affiche==1)
                   subplot(321);plot((oplo-oplo(1)));
                   hold on;plot(ltlo-ltlo(1));legend('OP','LTFB','location','southeast');ylabel('delay (ns)')
                   subplot(322);plot(ltre-ltre(1));legend('LTFB','location','southeast');ylabel('delay (ns)')
                   subplot(323);plot(opre-opre(1));legend('OP','location','southeast');ylabel('delay (ns)')
                   subplot(324);plot(abs(xval1));ylabel('|xval1|');line([k(1) k(1)],[0 max(abs(xval1))]);line([k(end) k(end)],[0 max(abs(xval1))])
                 end
               end
               if (gen_1s==1)
                 fo=fopen([num2str(ladate(p)),'.1s'],'w');
                 fprintf(fo,"# MJD\t\tOPlocal\tOPremote\tLTFBlocal\tLTBBremote\n");
                 cpt=0;
                 for k=1:25:length(opre)-25  % generate 1s files
                    [aoplo,boplo]=polyfit([k-1:k+25-2]/25,oplo(k:k+25-1),1);
                    [aopre,bopre]=polyfit([k-1:k+25-2]/25,opre(k:k+25-1),1);
                    [altlo,bltlo]=polyfit([k-1:k+25-2]/25,ltlo(k:k+25-1),1);
                    [altre,bltre]=polyfit([k-1:k+25-2]/25,ltre(k:k+25-1),1);
                    soloplo=boplo.yf(13); % 13=[0:25]/2
                    solopre=bopre.yf(13);
                    solltlo=bltlo.yf(13);
                    solltre=bltre.yf(13);
                    fprintf(fo,"%f\t%f\t%f\t%f\t%f\n",ladate(p)+cpt/86400,soloplo,solopre,solltlo,solltre);
                    cpt++;
                 end
                 fclose(fo);
               end
               res25=conv(res,ones(25,1)/25)(25:end-25);
               res252=conv(res2,ones(25,1)/25)(25:end-25);
               resmean25(p)=mean(res25);
               resmean252(p)=mean(res252);
               resstd25(p)=std(res25);
               resstd252(p)=std(res252);
               if (length(opre)>2)
                 opslope(:,p)=polyfit([0:length(opre)-1]/25,opre,1);
                 ltslope(:,p)=polyfit([0:length(opre)-1]/25,ltre,1);
                 if (length(res)>800)
                    [fftvalmax(p),fftmax(p)]=max(abs(fftshift(fft(res-mean(res))))(floor(length(res)/2):floor(length(res)/2)+400));
                 else
                    [fftvalmax(p),fftmax(p)]=max(abs(fftshift(fft(res-mean(res))))(floor(length(res)/2):end));
                 end
                 resf=fftshift(fft(res));
                 resf(floor(length(res)/2)-2+fftmax(p):floor(length(res)/2)+fftmax(p))=0;
                 res=real(ifft(fftshift(resf)));
                 resfiltm(p)=mean(res);
                 resfilts(p)=std(res);
                 res25=conv(res,ones(25,1)/25)(25:end-25);
                 resfmean25(p)=mean(res25);
                 resfstd25(p)=std(res25);
               end
             else  % if length(nomre)>0
               resmean(p)=NaN;
               resstd(p)=NaN;
               resmean25(p)=NaN;
               resstd25(p)=NaN;
               fftmax(p)=NaN;
               loplo(p)=NaN;
               lltlo(p)=NaN;
               ltslope(:,p)=NaN;
               opslope(:,p)=NaN;
               ladate(:,p)=NaN;
             end
          end % if (isempty(nom))  
  end
end
      else
        resmean(p)=NaN;
        resstd(p)=NaN;
        resmean25(p)=NaN;
        resstd25(p)=NaN;
        fftmax(p)=NaN;
        loplo(p)=NaN;
        lltlo(p)=NaN;
        ltslope(:,p)=NaN;
        opslope(:,p)=NaN;
        ladate(:,p)=NaN;
    end  % if length(oplo)>2
else
printf("\nexist\n");
end % exist
         p=p+1;
  end
      
    %k=find(resstd25>5);  % 1.65 ns
    %resmean(k)=NaN;resstd(k)=NaN;resmean25(k)=NaN;resstd25(k)=NaN;ltslope(:,k)=NaN;opslope(:,k)=NaN;fftmax(k)=NaN;snrop(k)=NaN;snrlt(k)=NaN;
    %k=find(abs(resmean>20));      % outliers
    %resmean(k)=NaN;resstd(k)=NaN;resmean25(k)=NaN;resstd25(k)=NaN;ltslope(:,k)=NaN;opslope(:,k)=NaN;fftmax(k)=NaN;snrop(k)=NaN;snrlt(k)=NaN;
  
    k=find(resstd25==0);  % 1.65 ns
    resmean(k)=NaN;
    resstd(k)=NaN;
    resmean25(k)=NaN;
    resmean252(k)=NaN;
    resstd25(k)=NaN;
    ltslope(:,k)=NaN;
    opslope(:,k)=NaN;
    fftmax(k)=NaN;
    snrop(k)=NaN;
    snrlt(k)=NaN;
    ladate(k)=NaN;
  
    k=find(abs(resmean==0));      % outliers
    resmean(k)=NaN;
    resstd(k)=NaN;
    resmean25(k)=NaN;
    resmean252(k)=NaN;
    resstd25(k)=NaN;
    ltslope(:,k)=NaN;
    opslope(:,k)=NaN;
    fftmax(k)=NaN;
    snrop(k)=NaN;
    snrlt(k)=NaN;
    ladate(k)=NaN;
  
    figure
    hold on
    subplot(211)
s=s=mod(resmean25,200/(2*N+1)/2);
k=find(s>10);s(k)=s(k)-200/(2*N+1)/2;
k=find(ladate-60000>904);
s(k)=s(k)+6.5;
k=find(ladate-60000>926.5);
s(k)=s(k)-5.5+1.29;
resmean25=s';
    errorbar(ladate-60000,s,resstd25)
    hold on
    plot(ladate-60000,s,'ro')
    xlim([829 max(ladate-60000)]);ylim([-1 10]);xlabel('MJD (day)');ylabel('TWSTFT delay (ns) @ 1 s')
    
    figure
    hold on
    subplot(211)
s=s=mod(resmean252,200/(2*N+1)/2);
k=find(s>10);s(k)=s(k)-200/(2*N+1)/2;
k=find(ladate-60000>904);
s(k)=s(k)+6.5;
k=find(ladate-60000>926.5);
s(k)=s(k)-5.5+1.29;
resmean252=s';
    errorbar(ladate-60000,s,resstd252)
    hold on
    plot(ladate-60000,s,'ro')
    xlim([829 max(ladate-60000)]);ylim([-1 10]);xlabel('MJD (day)');ylabel('TWSTFT delay (ns) polyfit')
    % load d_op_ltfb.txt 
    % errorbar(d_op_ltfb(:,1)-60000,d_op_ltfb(:,3)+resmean25(2),d_op_ltfb(:,4))
   
ladate=ladate';
save -text ladate ladate
save -text resmean25 resmean25
save -text resmean252 resmean252
 
    figure
    subplot(211)
    fftmax=fftmax*2.5e6/1e5./loplo;  % *coderate/codelength/filelength
    plot(ladate-60000,fftmax);
    xlabel('MJD-60000 (days)')
    ylabel('FFT max position (Hz)')
    ylim([0 2]);xlim([829 max(ladate-60000)]);
    subplot(212)
    plot(ladate-60000,ltslope(1,:));
    hold on
    plot(ladate-60000,opslope(1,:));
    ylabel('slope (ns/s)')
    xlabel('MJD-60000 (days)')
    xlim([829 max(ladate-60000)]);ylim([-10 10]);
    
    figure
    subplot(211)
    plot(ladate-60000,loplo(1,:));
    hold on
    plot(ladate-60000,lltlo(1,:));
    legend('OP','LTFB','location','southeast')
    ylabel('file size (bytes)')
    xlabel('MJD-60000 (days)')
    xlim([829 max(ladate-60000)]);
    
    figure
    subplot(211)
k=find(snrop<44);snrop(k)=NaN;
k=find(snrlt<44);snrlt(k)=NaN;
    plot(ladate-60000,snrop);
    hold on
    plot(ladate-60000,snrlt);
    legend('OP','LTFB','location','southwest')
    ylabel('C/N0 (dB.Hz)')
    xlabel('MJD-60000 (days)')
    xlim([829 max(ladate-60000)]);
    ylim([40 57])
  return
  
  load out_baptiste.dat
  errorbar(out_baptiste(:,1)-60000,out_baptiste(:,2)+resmean25(2),out_baptiste(:,3))
  xlabel('MJD-60000 (day)')
  ylabel("TW delay=\n0.5[(OPre-OPlo)-(LTFBre-LTFBlo)]")
  % legend('40 ms code','integration over 1 s','location','southwest')
  legend('integration over 1 s','location','southwest')
  ylim([-2 8])
  subplot(212)
  plot(ladate-60000,resstd25)
  xlabel('MJD-60000 (day)')
  ylabel('std(TW delay)')
  
  figure
  %errorbar(ladate-60000,resmean,resstd)
  hold on
  subplot(211)
  errorbar(ladate-60000,resmean25,resfstd25)
  hold on
  load d_op_ltfb.txt 
  errorbar(d_op_ltfb(:,1)-60000,d_op_ltfb(:,3)+resmean25(2),d_op_ltfb(:,4))
  xlabel('MJD-60000 (day)')
  ylabel("TW delay=\n0.5[(OPre-OPlo)-(LTFBre-LTFBlo)]")
  % legend('40 ms code','integration over 1 s','location','southwest')
  legend('integration over 1 s','location','southwest')
  ylim([-2 8])
  subplot(212)
  plot(ladate-60000,resfilts./resstd25)
  xlabel('MJD-60000 (day)')
  ylabel('std/std25(filtered)')
  
  
  return
  figure(3)
  subplot(211)
  %errorbar(ladate-60000,resmean25,resfstd25)
  load traffic
  for k=1:length(traffic)
    tmp=datevec(traffic(k,1)/86400+datenum('1/1/1970','mm/dd/yyyy'));
    tmp=julianDay(tmp(1),tmp(2),tmp(3)+(tmp(4)+tmp(5)/60+tmp(6)/3600)/24)-2400000.5 +2; % JMF +2 ?!
    ladatetraffic(k)=tmp;
  end
  subplot(212)
  plot(ladatetraffic(1:end-1)-60000,diff(traffic(:,2)))
  xlabel('MJD-60000 (days)');ylabel('Ethernet packets');
  
  figure
  
  k=find(resmean2<1000);
  resmean2(k)=resmean2(k)+1000;
  k=find(resmean2>500);
  resmean2(k)=resmean2(k)-1000;
  k=find(resmean2>50);
  resmean2(k)=resmean2(k)-100;
  k=find(resmean2<-50);
  resmean2(k)=resmean2(k)+100;
  plot(resmean2)
  ylim([0 10])
  hold on
  plot(resmean)
