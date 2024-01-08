graphics_toolkit('gnuplot')
clear all
close all
format long
dirlistrem=dir('./rem*mat.gz');
dirlistloc=dir('./loc*mat.gz');
dirlistOPrem=dir('../2401_OP/rem*mat.gz');
dirlistOPloc=dir('../2401_OP/loc*mat.gz');

for dirnum=1:length(dirlistrem)
  dirlistrem(dirnum).name
  eval(['load ',dirlistrem(dirnum).name]);
  r=(indice1+correction1/3);
  k=find(abs(xval1>max(abs(xval1)/2)));
  r=r(k(1):k(end));
  plot(r)
  title(strrep(dirlistrem(dirnum).name,'_',' '))
  figure
end

