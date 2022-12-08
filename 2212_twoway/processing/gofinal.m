pkg load signal
graphics_toolkit('gnuplot')  % beware of steps with fltk !
affiche=0;
fs=5e6;
Nint=1;

if exist('args')==1 
  filename=args{1}
  datename=args{3}
  dirnummat=1
else
  dirlistmat=dir('./1*mat');
  dirdate=dir('??????????');
  filename=dirlistmat(1).name
  datename=dirdate(1).name
  dirnummat=1
end
%for dirnummat=1:length(dirlistmat)
  clear code
  filename
  eval(['load ',filename])
  solution1=indice1+correction1_a;
  solution2=indice2+correction2_a;
  k=find(10*log10(SNR1i+SNR1r)>-15);
  solution1=solution1(k);
  solution2=solution2(k);
  SNR1r=SNR1r(k);
  SNR1i=SNR1i(k);
  SNR2r=SNR2r(k);
  SNR2i=SNR2i(k);
  df1=df1(k);
  df2=df2(k);
  solution=(solution1-solution2);
  [a,b]=polyfit([1:length(solution)],(solution)/(2*Nint+1)/fs,2);
  codelen(dirnummat)=length(code)/2;
  if ((affiche==1)||codelen(dirnummat)==250000)
    figure
    subplot(221)
    plot((solution)/(2*Nint+1)/fs); % ranging solution
    xlabel('time (s)')
    ylabel('ranging delay (s)')
    subplot(223)
    plot((solution)/(2*Nint+1)/fs-b.yf); % ranging solution
    legend(num2str(std((solution)/(2*Nint+1)/fs-b.yf)))
    xlabel('time (s)')
    ylabel('delay - parabolic fit (s)')
    subplot(222);plot(10*log10(SNR1r+SNR1i)(k))
    subplot(224);plot(10*log10(SNR2r+SNR2i)(k))
  end
  standard(dirnummat)=std((solution)/(2*Nint+1)/fs-b.yf);
  average(dirnummat)=mean((solution)/(2*Nint+1)/fs-b.yf);
  printf("%% y  m  d  h  m  s\tdelay\t\tdf1\tSNR1\tdf2\tSNR2\r\n");
  for p=1:length(SNR1i)
     % datestr(datenum([1970, 1, 1, 0, 0, 1670074201]))
     printf("%s\t%.12f\t%.1f\t%.1f\t%.1f\t%.1f\n",strftime("%Y %m %d %H %M %S", localtime(str2num(datename)-181+p*(length(code)/2)/2.5e6)),solution(p)/(2*Nint+1)/fs,df1(p),10*log10(SNR1i(p)+SNR1r(p)),df2(p),10*log10(SNR2i(p)+SNR2r(p)));
  end
[c,i]=sort(codelen);

figure
semilogx(c,standard(i)*1e9,'x-')
xlabel('code length (bits)')
ylabel('std(ranging) (ns)')
hold on
