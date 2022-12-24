pkg load signal
% graphics_toolkit('gnuplot')

fs=5e6;

dirlist=dir('./*bin')
dirbit=dir('./code/*bin')
for k=1:length(dirlist)
  dirbit(mod(k-1,length(dirbit))+1).name
  f=fopen(['code/',dirbit(mod(k-1,length(dirbit))+1).name]);
  code=fread(f,inf,'int8');
  code=repelems(code,[[1:length(code)] ; ones(1,length(code))*2]); % interpolate
  code=2*code-1;  % +1/-1
  fclose(f);

  f=fopen(dirlist(k).name);
  d=fread(f,fs*4*10,'int16');  % 1 second
  d=fread(f,fs*4*10,'int16');  % 1 second
  d=fread(f,fs*4*10,'int16');  % 1 second
  d=fread(f,5*length(code)*4,'int16');  % 1 second
%  d=fread(f,4*fs,'int16');  % 1 second
  d=d(1:2:end)+j*d(2:2:end);
  d1=d(1:2:end);  % measurement
  d2=d(2:2:end);  % reference
  d1=d1-mean(d1);
  d2=d2-mean(d2);
figure
  plot(abs(xcorr(d1,code(length(code)/2:end))))
  % plot(abs(xcorr(d1-mean(d1))))
std(real(d1))
std(real(d2))
  title([strrep(dirbit(mod(k-1,length(dirbit))+1).name,'_',' '),' ' ,strrep(dirlist(k).name,'_',' ')]);
  nom=strrep(dirlist(k).name,'.bin','.png');
  eval(['print -dpng /tmp/',nom])
end
