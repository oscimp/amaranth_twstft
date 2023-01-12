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
       difference=tempsop-tempsltfb
       ltfb=ltfb(difference+1:end,:);
       op=op(1:length(ltfb),:);
    else
       difference=tempsltfb-tempsop
       op=op(difference+1:end,:);
       ltfb=ltfb(1:length(op),:);
    end
    res=0.5*(ltfb(:,10)-ltfb(:,13)-(op(:,10)-op(:,13)));
    res=res*1e9;
    std(res(20:end))
    mean(res(20:end))
  else
    printf("No match\n");
  end
end
