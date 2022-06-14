t=[0:0.01:10];
s=(sin(2*pi*t));
sp=s;
s(100:400)=-s(100:400);
s(600:700)=-s(600:700);
s(900:1000)=-s(900:1000);
subplot(411)
plot(sp)
hold on
plot(s)
legend('carrier','BPSK')
xlim([0 1000]);xlabel('time (sample index)');ylabel('BPSK')
sq=(exp(j*2*pi*t));
sq(100:400)=sq(100:400).*exp(j*pi/2);
sq(600:700)=sq(600:700).*exp(-j*pi/2);
sq(900:1000)=sq(900:1000).*exp(j*pi);
subplot(412)
plot(real(sq));hold on
plot(imag(sq));
xlim([0 1000]);xlabel('time (sample index)');ylabel('QPSK');legend('I','Q')
subplot(413)
plot(real(sq)+imag(sq));
xlim([0 1000]);xlabel('time (sample index)');ylabel('QPSK');legend('I+Q')
subplot(414)
plot(linspace(-1,1,length(sq)),abs(fftshift(fft(real(sq)+imag(sq))))/2);
hold on
plot(linspace(-1,1,length(s)),abs(fftshift(fft(s))));
xlabel('normalized frequency (no unit)')
ylabel('|FFT| (a.u.)');legend('BPSK','QPSK')
