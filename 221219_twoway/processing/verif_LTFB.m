dd=dir('*.mat.gz');
p=1;
r=1;
for ll=1:length(dd)
  eval(['load ',dd(ll).name]);
  dd(ll).name
  if (length(df1)!=185) printf("ERREUR\n");end
  if strfind(dd(ll).name,"remote")
       df1r(r)=mean(df1(60:120));
       SNR1rem(r)=mean(10*log10(SNR1r+SNR1i)(60:120));
       p1cr(r)=mean(puissance1code(60:120));
       p1tr(r)=mean(puissance1total(60:120));
       tempsr(r)=str2num(strrep(dd(ll).name,'remote','')(1:10));
       delair=indice1+correction1_a;
       delair=delair(30:150)/15E6; % 2 minutes
       [a,b]=polyfit([30:150],delair,2);
       twm(r)=mean(delair);
       twe(r)=std(delair-b.yf);
       %if (twe(r)>2e-9)
       %   figure
       %   plot(delai-b.yf)
       %   title(dd(ll).name)
       %end
       r=r+1;
  else df1l(p)=mean(df1(60:120));df2l(p)=mean(df2(60:120));
       SNR1l(p)=mean(10*log10(SNR1r+SNR1i)(60:120));
       SNR2l(p)=mean(10*log10(SNR2r+SNR2i)(60:120));
       p1cl(p)=mean(puissance1code(60:120));
       p1tl(p)=mean(puissance1total(60:120));
       tempsl(p)=str2num(dd(ll).name(1:10));
       delai1=indice1+correction1_a;
       delai2=indice2+correction2_a;
       delai1=delai1(30:150)/15E6; % 2 minutes
       delai2=delai2(30:150)/15E6; % 2 minutes
       delai=delai1-delai2;
       [a,b]=polyfit([30:150],delai,2);
       ranging(p)=mean(delai);
       ecart(p)=std(delai-b.yf);
       delai2l(p)=mean(delai2);
       if (ecart(p)>2e-9)
          figure
          plot(delai-b.yf)
          title(dd(ll).name)
       end
       p=p+1; 
  end
end
k=find(twm<0);twm(k)=1+twm(k);
k=find(ranging<0);ranging(k)=1+ranging(k);

save -mat summary.mat 
graphics_toolkit('gnuplot');
subplot(411);plot(tempsl,ranging);    ylabel('tw delay (s)');   ylim([.26285 .263])
subplot(412);plot(tempsl,ecart*1E9);  ylabel('std(range) (ns)');ylim([0 2])
subplot(413);plot(tempsl,df1l);       ylabel('df (Hz)')
subplot(414);plot(tempsl,SNR1l);      ylabel('SNR (dB)');      
xlabel('unix time (s)');ylim([-25 0])

figure
subplot(411);plot(tempsr,twm-delai2l);ylabel('tw delay (s)');ylim([.2625 .2627])
subplot(412);plot(tempsr,twe*1E9);    ylabel('std(tw) (ns)');ylim([0 2])
subplot(413);plot(tempsr,df1r)   ;    ylabel('df (Hz)')     ;ylim([1600 1900]+50000)
subplot(414);plot(tempsr,SNR1rem);    ylabel('SNR (dB)');
xlabel('unix time (s)');ylim([-25 0])
