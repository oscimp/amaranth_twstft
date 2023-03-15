% graphics_toolkit('gnuplot')
format long
clear all
%close all

affiche=0;
Nint=1;  % interpolation = 2*Nint+1
codelen=1e5*2;
fs=5e6;
ltfbdir='./';
opdir='./';

dlop=dir(['./lo*.*.*.mat*gz']);
for l=1:length(dlop)
  dltfb=dir([dlop(l).name(1:13),'*.mat.gz']);
  if (length(dltfb)!=2)
     printf("No match\n");
  else
     dltfb=dltfb(2);
     dateltfb=num2str(str2num(dltfb.name(6:15))+180);
     dateltfb=eval(['dir(''',ltfbdir,(dateltfb(1:end-2)),'*end'')']);
     if (length(dateltfb)==0)
       printf("Failed to find end date of LTFB\n");
     else 
       printf("%s -> %s\n",dlop(l).name(6:15),dateltfb.name);
       dateltfb=str2num(dateltfb.name(1:end-4));
       dateop=str2num(dlop(l).name(17:26));
       eval(['load(''',dlop(l).name,''');']); % OP
       SNRopl=10*log10(SNR1r+SNR1i);
       topl=(indice1+correction1)/fs/(2*Nint+1);
       xopl=xval1;
       eval(['load(''',dltfb.name,''');']);   % LTFB
       SNRltfbl=10*log10(SNR1r+SNR1i);
       tltfbl=(indice1+correction1)/fs/(2*Nint+1);
       xltfbl=xval1;
       eval(['load(''',strrep(dlop(l).name,'local','remote'),''');']);
       SNRopr=10*log10(SNR1r+SNR1i);
       topr=(indice1+correction1)/fs/(2*Nint+1);
       xopr=xval1;
       eval(['load(''',strrep(dltfb.name,'local','remote'),''');']);   % LTFB
       SNRltfbr=10*log10(SNR1r+SNR1i);
       tltfbr=(indice1+correction1)/fs/(2*Nint+1);
       xltfbr=xval1;
   
       sizeop=7.2E9; % dir(strrep(dlop(l).name,'mat.gz','bin')(6:end)).bytes;
       dateop=dateop-sizeop/4/fs/2;  % 4 for complex short, 2 for 2 channels
       sizeltfb=7.4E9; % dir([ltfbdir,strrep(dltfb.name,'mat.gz','bin')(6:end)]).bytes;
       dateltfb=dateltfb-sizeltfb/4/fs/2;  % beginning date

       % check that OP TX (loopback) is consistent with LTFB RX (remote)
       kop=find(abs(xopl)>max(abs(xopl))/2);kop=kop(1);  % SNR criterion: remove beginning & end
       kltfb=find(abs(xltfbr)>max(abs(xltfbr))/2);kltfb=kltfb(1);  % SNR criterion: remove beginning & end
       if (abs(dateltfb+kltfb*codelen/fs-(dateop+kop*codelen/fs))>1)
	       printf("ERREUR OP\n");
          dateltfb+kltfb*codelen/fs
          dateop+kop*codelen/fs
       end
       % check that OP RX (remote) is consistent with LTFB TX (local)
       kltfb=find(abs(xltfbl)>max(abs(xltfbl))/2);kltfb=kltfb(1);  % SNR criterion: remove beginning & end
       kop=find(abs(xopr)>max(abs(xopr))/2);kop=kop(1);  % SNR criterion: remove beginning & end
       if (abs(dateltfb+kltfb*codelen/fs-(dateop+kop*codelen/fs))>1)
	       printf("ERREUR LTFB\n");
          dateltfb+kltfb*codelen/fs
          dateop+kop*codelen/fs
       end

       % realign sequences
       kltfbl=find(abs(xltfbl)>max(abs(xltfbl))/2);kltfbl=kltfbl(1);  % loopback of LTFB TX
       kltfbr=find(abs(xltfbr)>max(abs(xltfbr))/2);kltfbr=kltfbr(1);  % OP received by LTFB
       if (kltfbl>kltfbr)  % LTFB emits after OP
	       printf("PROBLEM?\n");
          kop=find(abs(xopr)>max(abs(xopr))/2);kop=kop(1);  % SNR criterion: remove beginning & end
          kltfb=find(abs(xltfbl)>max(abs(xltfbl))/2);kltfb=kltfb(1);  % SNR criterion: remove beginning & end
       else
          kop=find(abs(xopl)>max(abs(xopl))/2);kop=kop(1);  % SNR criterion: remove beginning & end
          kltfb=find(abs(xltfbr)>max(abs(xltfbr))/2);kltfb=kltfb(1);  % SNR criterion: remove beginning & end
       end
       topl=topl(kop:end);          topr=topr(kop:end);
       tltfbl=tltfbl(kltfb:end);    tltfbr=tltfbr(kltfb:end);
       SNRopl=SNRopl(kop:end);      SNRopr=SNRopr(kop:end);
       SNRltfbl=SNRltfbl(kltfb:end);SNRltfbr=SNRltfbr(kltfb:end);

       % adjust data length
       if (length(topl)>length(tltfbl))
          topl=topl(1:length(tltfbl));
          topr=topr(1:length(tltfbl));
       else
          tltfbl=tltfbl(1:length(topl));
          tltfbr=tltfbr(1:length(topl));
       end
       if (length(topl)>length(topr))
          topl=topl(1:length(topr));
          tltfbl=tltfbl(1:length(topr));
          tltfbr=tltfbr(1:length(topr));
       end
       if (length(topr)>length(topl))
          topl=topl(1:length(topl));
          tltfbl=tltfbl(1:length(topl));
          tltfbr=tltfbr(1:length(topl));
       end
        s=(tltfbr-tltfbl-(topr-topl))/2; % no impact since both OP and LTFB are shifted
%       s=((tltfbr(6:end)-tltfbl(1:end-6+1)-(topr(6:end)-topl(1:end-6+1)))/2); no impact since both OP and LTFB are shifted
%       s=((tltfbr(1:end-6+1)-tltfbl(6:end)-(topr(1:end-6+1)-topl(6:end)))/2);
       k=find(s<1/fs/2/(2*Nint+1));s(k)=s(k)+1/fs/2/(2*Nint+1);  % WHY 2 ?! because 1/2(...) above
       k=find(s>1/fs/2/(2*Nint+1));s(k)=s(k)-1/fs/2/(2*Nint+1);  % 
       k=find((s<2/fs/2/(2*Nint+1))&(s>-1/fs/2/(2*Nint+1)));s=s(k); 
       if (affiche==1)
          figure;subplot(211);plot(s(30:end))
          subplot(212);plot(SNRopl);hold on;plot(SNRltfbl);plot(SNRopr);plot(SNRltfbr);
       end
       moy(l)=mean(s);
       temps(l)=dateltfb;
%       std(conv(s(20:end-20),ones(25,1)/25)(20:end-20))
     end
  end
end
k=find(temps==0);temps(k)=NaN;
plot(temps,moy,'x')
