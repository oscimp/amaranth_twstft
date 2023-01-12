pkg load signal
affiche=0;
fs=5e6;
Nint=1;

if (affiche==1)
  graphics_toolkit('gnuplot')  % beware of steps with fltk !
end

localdirop='./op/'
remotedirop='./remote/'    % MUST include trailing /

if (exist('args')==1)
  localop=args{1}
  remoteop=args{2}
  localltfb=args{3}
  remoteltfb=args{4}
  dirlistmatltfb=localltfb;
else
  dirlistmatop=dir([localdirop,'/1*mat.gz*']); % exclude remote*
end

for dirnummat=1:length(dirlistmatop) 
if (1==0)
%%% start LTFB: local
  filenameltfb=[localdirltfb,dirlistmatltfb(dirnummat).name];
  dateltfb=str2num(dirlistendltfb(dirnummat).name(1:10));
  clear code
  eval(['load ',filenameltfb])
  solution1lo=indice1+correction1;          % ranging
  solution2lo=indice2+correction2;          % reference channel = loopback
  df1lo=df1;
  df2lo=df2;
  SNR1lo=10*log10(SNR1r+SNR1i);
  SNR2lo=10*log10(SNR2r+SNR2i);
% arbitrarily keep max(SNR)-10 to remove initial record when TX inactive
  dateini=dateltfb-length(solution1lo)+1; % seconds since 1/1/1970 from loopback
%%% start LTFB: remote
  filenameltfb=[remotedirltfb,dirlistmatltfb(dirnummat).name];
  eval(['load ',filenameltfb])
  solution1remote=indice1+correction1;
  SNR1remote=10*log10(SNR1r+SNR1i);           % two-way

  foutname=strrep(dirlistmatltfb(dirnummat).name,'.mat.gz','ltfb.txt');
  fout=fopen(foutname,"w"); 
  fprintf(fout,"%% y  m  d  h  m  s\tdelay\t\tdf1\tSNR1\tdf2\tSNR2\tdelayrem\t\tdf1rem\tSNR1rem\r\n");
  for p=1:length(SNR2i)
     % datestr(datenum([1970, 1, 1, 0, 0, 1670074201]))
     fprintf(fout,"%s\t%.12f\t%.3f\t%.1f\t%.12f\t%.3f\t%.1f\t%.12f\t%.3f\t%.1f\n",strftime("%Y %m %d %H %M %S", localtime(dateini+p*(length(code)/2)/2.5e6)),solution1lo(p)/(2*Nint+1)/fs,df1lo(p),SNR1lo(p),solution2lo(p)/(2*Nint+1)/fs,df2lo(p),SNR2lo(p),solution1remote(p)/(2*Nint+1)/fs,df1(p),SNR1remote(p));
  end
  ltfbtw=(solution1remote-solution2lo)/(2*Nint+1)/fs; % tw-loopback
  fclose(fout);
%%% the end for both LTFB
end

%%% start OP: remote
  filenameop=[remotedirop,dirlistmatop(dirnummat).name];
  if (isempty(filenameop))
     printf("No match !\n");
  else
     eval(['load ',filenameop])
     solution1remote=indice1+correction1_a;
     SNR1remote=10*log10(SNR1r+SNR1i);
     df1remote=df1;
     k=find(SNR1remote>max(SNR1remote)-10); 
     dateop=str2num(dirlistmatop(dirnummat).name(12:21));
     dateiniop=dateop-length(indice1)+1; % seconds since 1/1/1970 from loopback
%%% start OP: local
     clear code
     eval(['load ',localdirop,dirlistmatop(dirnummat).name])
     solution1lo=indice1+correction1_a;
     solution2lo=indice2+correction2_a;          % reference channel
     df1lo=df1;
     df2lo=df2;
     SNR1lo=10*log10(SNR1r+SNR1i);
     SNR2lo=10*log10(SNR2r+SNR2i);
% arbitrarily keep max(SNR)-10 to remove initial record when TX inactive

     foutname=strrep(dirlistmatop(dirnummat).name,'.mat.gz','op.txt');
     fout=fopen(foutname,"w"); 
     fprintf(fout,"%% y  m  d  h  m  s\tdelay\t\tdf1\tSNR1\tdf2\tSNR2\tdelayrem\t\tdf1rem\tSNR1rem\r\n");
     for p=1:length(SNR2i)
     % datestr(datenum([1970, 1, 1, 0, 0, 1670074201]))
        fprintf(fout,"%s\t%.12f\t%.3f\t%.1f\t%.12f\t%.3f\t%.1f\t%.12f\t%.3f\t%.1f\n",strftime("%Y %m %d %H %M %S", localtime(dateiniop+p*(length(code)/2)/2.5e6)),solution1lo(p)/(2*Nint+1)/fs,df1lo(p),SNR1lo(p),solution2lo(p)/(2*Nint+1)/fs,df2lo(p),SNR2lo(p),solution1remote(p)/(2*Nint+1)/fs,df1remote(p),SNR1remote(p));
     end
     fclose(fout);
  end
end
%%% the end for both OP
return
subplot(211);
k=find(moyenne<-0.5);moyenne(k)=moyenne(k)+1;
k=find(ladate>0);
plot(ladate(k),moyenne(k)*1e9);ylim([60 100]);ylabel("<tw delay> (ns)")
subplot(212);
plot(ladate(k),ecart(k)*1e9);ylim([0 5]);ylabel("std(tw) (ns)");xlabel('unix time (s)')
