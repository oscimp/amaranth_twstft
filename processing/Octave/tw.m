dirop='OP/'
dirltfb='LTFB/'

graphics_toolkit('gnuplot')

affiche=0;
m=1;

dop=dir([dirop,'*.*.*.txt']);
for l=1:length(dop)
  eval(['op=load(''',dirop,dop(l).name,''');']);
  dltfb=dir([dirltfb,dop(l).name(1:8),'*ltfb.txt']);
  if (isempty(dltfb)==0)
    printf("%s <> %s: ",dop(l).name,dltfb(1).name);
    eval(['ltfb=load(''',dirltfb,dltfb(1).name,''');']);
    tempsop=((((op(1,2)*31+op(1,3))*24)+op(1,4)*60)+op(1,5)*60)+op(1,6);
    tempsltfb=((((ltfb(1,2)*31+ltfb(1,3))*24)+ltfb(1,4)*60)+ltfb(1,5)*60)+ltfb(1,6);
    if (tempsop>tempsltfb)
       difference=tempsop-tempsltfb;
       ltfb=ltfb(difference+1:end,:);
       if (length(ltfb)>length(op)) ltfb=ltfb(1:length(op),:);end
       op=op(1:length(ltfb),:);
    else
       difference=tempsltfb-tempsop;
       op=op(difference+1:end,:);
       if (length(op)>length(ltfb)) op=op(1:length(ltfb),:);end
       ltfb=ltfb(1:length(op),:);
    end
    printf(" diff=%d\n",difference)
    if (difference<10)
      k=find(ltfb(:,9)>max(ltfb(:,9)-10));k=[k(1)+1:k(end)-1];  % SNR criterion: remove beginning & end
      ltfb=ltfb(k,:); op=op(k,:);
      k=find(op(:,9)>max(op(:,9)-10));k=[k(1)+1:k(end)-1];      % SNR criterion: remove beginning & end
      ltfb=ltfb(k,:); op=op(k,:);
      if (mean(ltfb(:,10)-ltfb(:,13))<0) ltfb(:,10)=ltfb(:,10)+1;end
      if (mean(op(:,10)-op(:,13))<0) op(:,10)=op(:,10)+1;end
      res=0.5*(ltfb(:,10)-ltfb(:,13)-(op(:,10)-op(:,13)));
      k=find(abs(res)<1e-6);
      if (isempty(k)) printf("%.12f\n",mean(res)*1e9);
      end
      res=res(k);
      if (affiche==1)
         if (std(res)<1e-6)
           figure
  	 % subplot(8,1,m)
           plot(res*1e9);
           xlabel('sample number (s)');ylabel('tw difference (ns)');title([dop(l).name,' - ',dltfb(1).name]);
  	 legend(['std=',num2str(std(res)),' <.>=',num2str(mean(res))]);
         end
      end
      res=res*1e9;
      if (std(res)<1E3)
        std(res)
        mean(res)
        sta(m)=std(res);
        moy(m)=mean(res);
        temps(m)=str2num(dltfb(1).name(1:10))/86400+40587;
	[uu(m),vv(m)]=max(abs(fft(res-mean(res)))(1:20));
      else
        if (affiche==1)
          figure
          subplot(311)
          plot(ltfb(:,10)-ltfb(:,13))
          subplot(312)
          plot(op(:,10)-op(:,13));
          subplot(313)
          plot(res)
        end
        std(res)
      end
    end
    m=m+1;
  else
    printf("%s: no match\n",dop(l).name);
  end
end

if (affiche==1)
  figure
  k=find(temps>0);
  subplot(311);plot(temps(k)-59000,moy(k),'x');ylabel('<tw> (ns)')
  subplot(312);plot(temps(k)-59000,sta(k),'x');ylabel('std(tw) (ns)');xlabel('MJD-59000 (days)')
  k=find(vv>0);
  subplot(313);plot(temps(k)-59000,vv(k),'x');ylabel('FFT(tw)');xlabel('MJD-59000 (days)')
end

