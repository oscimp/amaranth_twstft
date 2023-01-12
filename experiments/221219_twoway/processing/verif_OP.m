dd=dir('*.mat.gz');
p=1;
r=1;
for ll=1:length(dd)
  eval(['load ',dd(ll).name]);
  dd(ll).name
if (length(df1)!=185) printf("ERREUR"),
else
  if (length(df1)!=185) printf("ERREUR\n");end
  df1l(p)=mean(df1(60:120));df2l(p)=mean(df2(60:120));
  SNR1l(p)=mean(10*log10(SNR1r+SNR1i)(60:120));
  SNR2l(p)=mean(10*log10(SNR2r+SNR2i)(60:120));
  p1cl(p)=mean(puissance1code(60:120));
  p1tl(p)=mean(puissance1total(60:120));
  temps(p)=str2num(dd(ll).name(1:10));
  delai=((indice1+correction1_a-indice2-correction2_a)/15e6);
  moy(p)=mean(delai(30:150));
  [a,b]=polyfit([30:150],delai(30:150),2);
  eca(p)=std(delai(30:150)-b.yf);
  p=p+1; 
end
end
k=find(moy<0);moy(k)=1+moy(k);
save -mat summary.mat df1l df2l SNR1l SNR2l p1c* p1t* temps moy eca

graphics_toolkit('gnuplot');
subplot(411);plot(temps,moy);     ylabel('tw delay (s)');   ylim([.26225 .2624])
subplot(412);plot(temps,eca*1E9); ylabel('std(range) (ns)');ylim([0 2])
subplot(413);plot(temps,df1l);    ylabel('df (Hz)')
subplot(414);plot(temps,SNR1l);   ylabel('SNR (dB)');      
xlabel('unix time (s)');ylim([-25 0])
