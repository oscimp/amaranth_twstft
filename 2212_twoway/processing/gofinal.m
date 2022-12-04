pkg load signal
graphics_toolkit('gnuplot')  % beware of steps with fltk !
affiche=0;
fs=5e6;
Nint=1;

dirlistmat=dir('./*mat')
for dirnummat=1:length(dirlistmat)
  clear code
  dirlistmat(dirnummat).name
  eval(['load ',dirlistmat(dirnummat).name])
  solution1=indice1+correction1_a;
  solution2=indice2+correction2_a;
  k=find(10*log10(SNR1i+SNR1r)>-10);
  solution1=solution1(k);
  solution2=solution2(k);
  solution=solution1-solution2;
  [a,b]=polyfit([1:length(solution)],(solution)/(2*Nint+1)/fs,2);
  if (affiche==1)
    figure
    subplot(211)
    plot((solution)/(2*Nint+1)/fs); % ranging solution
    xlabel('time (s)')
    ylabel('ranging delay (s)')
    subplot(212)
    plot((solution)/(2*Nint+1)/fs-b.yf); % ranging solution
    legend(num2str(std((solution)/(2*Nint+1)/fs-b.yf)))
    xlabel('time (s)')
    ylabel('delay - parabolic fit (s)')
  end
  standard(dirnummat)=std((solution)/(2*Nint+1)/fs-b.yf);
  average(dirnummat)=mean((solution)/(2*Nint+1)/fs-b.yf);
end
codelen=[100000 1000 2500000 250000 25000 500000 5000];
[c,i]=sort(codelen);

figure
plot(c,standard(i),'x-')
xlabel('code length (bits)')
ylabel('std(ranging) (s)')
