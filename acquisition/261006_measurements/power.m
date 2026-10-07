rbw=1e3; % 1 kHz BW

d=dir('*DAT');
for l=1:length(d)
  x=dlmread(d(l).name,';',30,0);
  df=x(2,1)-x(1,1);
  pow=10.^(x(:,2)/10);
  printf("%s\t%.0f\t%.1f\n",d(l).name,df,10*log10(sum(pow/1e3*df)))
end
