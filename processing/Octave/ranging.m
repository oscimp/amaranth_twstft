dirop='OP/'
dirltfb='LTFB/'

dop=dir([dirop,'*.*.*.txt']);
for l=1:length(dop)
  eval(['op=load(''',dirop,dop(l).name,''');']);
  dltfb=dir([dirltfb,dop(l).name(1:7),'*ltfb.txt']);
  if (isempty(dltfb)==0)
    printf("%s <> %s: ",dop(l).name,dltfb(1).name)
    eval(['ltfb=load(''',dirltfb,dltfb(1).name,''');']);
    tempsop=((((op(1,2)*31+op(1,3))*24)+op(1,4)*60)+op(1,5)*60)+op(1,6);
    tempsltfb=((((ltfb(1,2)*31+ltfb(1,3))*24)+ltfb(1,4)*60)+ltfb(1,5)*60)+ltfb(1,6);
    if (tempsop>tempsltfb)
       difference=tempsop-tempsltfb;
       ltfb=ltfb(difference+1:end,:);
       op=op(1:length(ltfb),:);
    else
       difference=tempsltfb-tempsop;
       op=op(difference+1:end,:);
       ltfb=ltfb(1:length(op),:);
    end
    res=(ltfb(:,10)-ltfb(:,7));
    res=res(10:end);
    [a,b]=polyfit([1:length(res)]',res,2);
    printf("diff=%d stdLTFB=%f ",difference,std((res-b.yf)*1e9));
    printf("<LTFB>=%f ",mean(1-res));
    res=(op(:,10)-op(:,7));
    res=res(10:end);
    [a,b]=polyfit([1:length(res)]',res,2);
    printf("stdOP=%f ",std((res-b.yf)*1e9))
    printf("<OP>=%f\n",mean(1-res))
  else
    printf("No match\n");
  end
end
