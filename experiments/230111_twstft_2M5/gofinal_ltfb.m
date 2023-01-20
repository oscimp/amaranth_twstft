pkg load signal
format long
affiche=0;
fs=5e6;
Nint=1;
global code=ones(fs,1); % needed if not stored in .mat archive, will be overwritten otherwise

if (affiche==1)
%  graphics_toolkit('gnuplot')  % beware of steps with fltk !
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
end

for dirnummat=1:length(dirlistmatltfb) 
%%% start LTFB: local
  filenameltfb=[localdirltfb,dirlistmatltfb(dirnummat).name]
  dirlistendltfb=dir([localdirltfb,num2str(str2num(dirlistmatltfb(dirnummat).name(1:10))+180)(1:8),'*end']); % exclude remote*
  dateltfb=str2num(dirlistendltfb(1).name(1:10));
  if (isempty(dir([localdirltfb,dirlistmatltfb(dirnummat).name(1:10),'*txt'])))  % dont process files that have already been processed
    % clear code
    eval(['load ',filenameltfb])
    if (isempty(strfind(filenameltfb,"C"))) % file resulting from Octave script processing
      solution1lo=indice1+correction1;      % ranging
      solution2lo=indice2+correction2;      % reference channel = loopback
      SNR1lo=10*log10(SNR1r+SNR1i);
      SNR2lo=10*log10(SNR2r+SNR2i);
    else                                    % file resulting from C program processing
      solution1lo=correction1';              % ranging
      solution2lo=correction2';              % reference channel = loopback
      SNR1lo=SNR1';
      SNR2lo=SNR2';
    end
    df1lo=df1;
    df2lo=df2;
  % arbitrarily keep max(SNR)-10 to remove initial record when TX inactive
    dateini=dateltfb-length(solution1lo);    % seconds since 1/1/1970 from loopback: storage end = final date + 1 s

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
    printf("stdLTFB=%f\t",std((res-b.yf)*1e9));
    moy=mean(res);
    if (moy<0) moy=moy+1;end
    printf("<LTFB>=%f\n",moy);
  % end of filtering

  %%% start LTFB: remote
    filenameltfb=[remotedirltfb,dirlistmatltfb(dirnummat).name];
    eval(['load ',filenameltfb])
    if (isempty(strfind(filenameltfb,"C")))
      solution1remote=indice1+correction1;
      SNR1remote=10*log10(SNR1r+SNR1i);           % two-way
    else
      solution1remote=correction1;
      SNR1remote=SNR1;           % two-way
    end
  
    foutname=strrep(dirlistmatltfb(dirnummat).name,'.mat.gz','ltfb.txt');
    fout=fopen(foutname,"w"); 
    fprintf(fout,"%% y  m  d  h  m  s\tdelay\t\tdf1\tSNR1\tdf2\tSNR2\tdelayrem\t\tdf1rem\tSNR1rem\r\n");
    for p=indices % 1:length(SNR1lo)
       % datestr(datenum([1970, 1, 1, 0, 0, 1670074201]))
       fprintf(fout,"%s\t%.12f\t%.3f\t%.1f\t%.12f\t%.3f\t%.1f\t%.12f\t%.3f\t%.1f\n",strftime("%Y %m %d %H %M %S", localtime(dateini+(p-1)*(length(code)/2)/2.5e6)),solution1lo(p)/(2*Nint+1)/fs,df1lo(p),SNR1lo(p),solution2lo(p)/(2*Nint+1)/fs,df2lo(p),SNR2lo(p),solution1remote(p)/(2*Nint+1)/fs,df1(p),SNR1remote(p));
    end
    fclose(fout);
  else
    printf("already processed\n");
  end
%%% the end for both LTFB
end
