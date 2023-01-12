pkg load signal
affiche=0;
fs=5e6;
Nint=1;

if (affiche==1)
  graphics_toolkit('gnuplot')  % beware of steps with fltk !
end

localdirop='OP/res/op/'
remotedirop='OP/res/remote/'    % MUST include trailing /
localdirltfb='LTFB/'
remotedirltfb='LTFB/remote' % no / since LTFB includes remote in filename

if (exist('args')==1)
  localop=args{1}
  remoteop=args{2}
  localltfb=args{3}
  remoteltfb=args{4}
  dirlistmatltfb=localltfb;
else
  dirlistmatltfb=dir([localdirltfb,'/1*mat.gz*']); % exclude remote*
  dirlistendltfb=dir([localdirltfb,'/1*end*']); % exclude remote*
end

for dirnummat=1:length(dirlistmatltfb) 
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

if (1==0)
%%% start OP: remote
  filenameop=dir([remotedirop,num2str(dateltfb)(1:end-2),'*']);
  if (isempty(filenameop))
     printf("No match !\n");
  else
     printf("%s <> %s\n",filenameltfb,filenameop.name)
     eval(['load ',remotedirop,filenameop.name])
     solution1remote=indice1+correction1;
     SNR1remote=10*log10(SNR1r+SNR1i);
     df1remote=df1;
     k=find(SNR1remote>max(SNR1remote)-10); 
     dateiniop=dateiniltfb-k(1)+1; % ranging LTFB = ranging OP
%%% start OP: local
     clear code
     eval(['load ',localdirop,filenameop.name])
     solution1lo=indice1+correction1;
     solution2lo=indice2+correction2;          % reference channel
     df1lo=df1;
     df2lo=df2;
     SNR1lo=10*log10(SNR1r+SNR1i);
     SNR2lo=10*log10(SNR2r+SNR2i);
% arbitrarily keep max(SNR)-10 to remove initial record when TX inactive

     foutname=strrep(filenameop.name,'.mat.gz','op.txt');
     fout=fopen(foutname,"w"); 
     fprintf(fout,"%% y  m  d  h  m  s\tdelay\t\tdf1\tSNR1\tdf2\tSNR2\tdelayrem\t\tdf1rem\tSNR1rem\r\n");
     for p=1:length(SNR2i)
     % datestr(datenum([1970, 1, 1, 0, 0, 1670074201]))
        fprintf(fout,"%s\t%.12f\t%.3f\t%.1f\t%.12f\t%.3f\t%.1f\t%.12f\t%.3f\t%.1f\n",strftime("%Y %m %d %H %M %S", localtime(dateiniop+p*(length(code)/2)/2.5e6)),solution1lo(p)/(2*Nint+1)/fs,df1lo(p),SNR1lo(p),solution2lo(p)/(2*Nint+1)/fs,df2lo(p),SNR2lo(p),solution1remote(p)/(2*Nint+1)/fs,df1remote(p),SNR1remote(p));
     end
     fclose(fout);
     optw=(solution1remote-solution2lo)(k)/(2*Nint+1)/fs; % tw-loopback
     if (length(optw)<length(ltfbtw)) longueur=length(optw); else longueur=length(ltfbtw);end;
     tw=optw(1:longueur)-ltfbtw(1:longueur);
     moyenne(dirnummat)=mean(tw);
     ecart(dirnummat)=std(tw);
     ladate(dirnummat)=dateiniop;
end
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
