% OP
f=fopen('1704367541_1704367876.115458377.bin');fseek(f,5e6*4*2*60);d=fread(f,1e5,'int16');
std(d(1:4:end))
std(d(3:4:end))
%ans = 1581.9 remote
%ans = 551.90 loopback

% LTFB
f=fopen('1704367542_1704367883.996582594.bin');fseek(f,5e6*4*2*60);d=fread(f,1e5,'int16');
std(d(1:4:end))
std(d(3:4:end))
%ans = 2986.2 loopback
%ans = 5148.2 remote
