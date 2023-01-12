close all
clear all

fs=25e6;
load godual_ranging_LTFB_interp5.mat
obob1=indice1+correction1_1;
obob2=indice2+correction2_1;
load godual_ranging_OP_interp5.mat
opop1=indice1+correction1_1;
opop2=indice2+correction2_1;
load godual_txLTFB_rxOP_interp5.mat
obop1=indice1+correction1;
load godual_txOP_rxLTFB_interp5.mat
opob1=indice1+correction1;

clear x* c* df ind*

mean((obob1-obob2)/fs) % ranging besancon     0.2629 ms
mean((opop1-opop2)/fs) % ranging paris        0.2623 ms
mean((obop1-opop2)(10:end-10)/fs) % TX besancon-RX paris 0.2626 ms doit etre 262
mean((opob1-obob2)(20:end-20)/fs) % TX paris-RX besancon 0.2626 ms

subplot(411)
plot((obob1-obob2)/fs)
subplot(412)
plot((opop1-opop2)/fs)
subplot(413)
plot((obop1-opop2)(10:end-10)/fs) % two-way - ranging TX Besancon
subplot(414)
plot((opob1-obob2)(20:end-20)/fs) % two-way - ranging TX Paris
figure
plot(((obop1-opop2)(20:160)/fs-((opob1-obob2)(20:160)/fs))/2) % TX paris-RX besancon 0.2626 ms
mean(((obop1-opop2)(20:160)/fs-((opob1-obob2)(20:160)/fs))/2) % TX paris-RX besancon 0.2626 ms
std(((obop1-opop2)(20:160)/fs-((opob1-obob2)(20:160)/fs))/2) % TX paris-RX besancon 0.2626 ms
