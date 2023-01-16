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

%%% start OP: remote
  filenameop=[remotedirop,dirlistmatop(dirnummat).name]
  if (isempty(filenameop))
     printf("No match !\n");
  else
   if (isempty(dir(['../',strrep(dirlistmatop(dirnummat).name,'.mat.gz','op.txt')])))
     eval(['load ',filenameop])
     solution1remote=indice1+correction1_a;
     SNR1remote=10*log10(SNR1r+SNR1i);
     df1remote=df1;
     k=find(SNR1remote>max(SNR1remote)-10); 
     dateop=str2num(dirlistmatop(dirnummat).name(12:21));
     dateiniop=dateop-length(indice1); % seconds since 1/1/1970 from loopback
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
     
   % filter to only keep relevant items
     indices=find(SNR1lo>max(SNR1lo)-10);
     res=(solution1lo(indices)-solution2lo(indices))/fs/(2*Nint+1);
     [a,b]=polyfit([1:length(res)],res,2);
     if (std(res-b.yf)>1e-6)
        indices1=find((abs(res-mean(res(30:40))))<1e-5);   % 5 ns/s = 900 ns/3 min
        indices2=find((abs(res-mean(res(140:150))))<1e-5);
        if (!isempty(indices1) && (!isempty(indices2)))
          if (length(indices1)>length(indices2)) indices=indices1;else indices=indices2;end;
          res=res(indices);
          [a,b]=polyfit([1:length(res)],res,2);
          printf("keep %d samples ",length(indices));
	  res(1:5)
	  res(end-5:end)
	end
     end
     printf("stdOP=%f\t",std((res-b.yf)*1e9));
     moy=mean(res);
     if (moy<0) moy=moy+1;end
     printf("<OP>=%f\n",moy);
   % end of filtering

     foutname=strrep(dirlistmatop(dirnummat).name,'.mat.gz','op.txt');
     fout=fopen(foutname,"w"); 
     fprintf(fout,"%% y  m  d  h  m  s\tdelay\t\tdf1\tSNR1\tdf2\tSNR2\tdelayrem\t\tdf1rem\tSNR1rem\r\n");
     for p=1:length(SNR2i)
     % datestr(datenum([1970, 1, 1, 0, 0, 1670074201]))
        fprintf(fout,"%s\t%.12f\t%.3f\t%.1f\t%.12f\t%.3f\t%.1f\t%.12f\t%.3f\t%.1f\n",strftime("%Y %m %d %H %M %S", localtime(dateiniop+(p-1)*(length(code)/2)/2.5e6)),solution1lo(p)/(2*Nint+1)/fs,df1lo(p),SNR1lo(p),solution2lo(p)/(2*Nint+1)/fs,df2lo(p),SNR2lo(p),solution1remote(p)/(2*Nint+1)/fs,df1remote(p),SNR1remote(p));
     end
     fclose(fout);
   else
     printf("Already done\n");
   end
  end
end
%%% the end for both OP
