from pathlib import Path

p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java")
s=p.read_text()

# Adiciona helper de altura adaptativa dentro da Pane, antes de render()
marker='''        void render(){'''
helper=r'''        void updateListHeightSmart(){
            try{
                int countItems=visibleNodes.size();
                LinearLayout.LayoutParams lp=(LinearLayout.LayoutParams)list.getLayoutParams();

                if(countItems==0){
                    // Lista vazia não pode ocupar uma área invisível e roubar o gesto do ScrollView pai.
                    list.setVisibility(View.GONE);
                    lp.height=0;
                    list.setLayoutParams(lp);
                    return;
                }

                list.setVisibility(View.VISIBLE);

                int maxH=Math.max(dp(190),Math.min(dp(340),getResources().getDisplayMetrics().heightPixels/3));
                int width=list.getWidth();
                if(width<=0) width=Math.max(dp(240),getResources().getDisplayMetrics().widthPixels-dp(64));

                int total=0;
                int divider=Math.max(0,list.getDividerHeight());
                int measureCount=Math.min(countItems,8);

                for(int i=0;i<measureCount;i++){
                    View child=fileAdapter.getView(i,null,list);
                    int wSpec=View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY);
                    int hSpec=View.MeasureSpec.makeMeasureSpec(0,View.MeasureSpec.UNSPECIFIED);
                    child.measure(wSpec,hSpec);
                    total+=child.getMeasuredHeight();
                    if(i>0) total+=divider;
                    if(total>=maxH)break;
                }

                // Se os poucos itens cabem, a ListView fica exatamente do tamanho deles.
                // Assim qualquer área abaixo pertence ao ScrollView principal.
                if(countItems<=measureCount && total<maxH){
                    lp.height=Math.max(dp(1),total);
                }else{
                    lp.height=maxH;
                }

                list.setLayoutParams(lp);
            }catch(Throwable e){
                BiggerApp.logNonFatal(MainActivity.this,"FILE_MANAGER","Altura adaptativa da lista",e);
            }
        }

'''
if marker not in s:
    raise SystemExit("render marker não encontrado")
s=s.replace(marker,helper+marker,1)

# Chama após atualizar adapter e antes do contador
old='''            fileAdapter.notifyDataSetChanged();
            try{list.setFastScrollEnabled(visibleNodes.size()>100);}catch(Throwable e){BiggerApp.logNonFatal(MainActivity.this,"FILE_MANAGER","Fast scroll",e);}
            count.setText(visibleNodes.size()+" itens • "+selected.size()+" selecionados");'''
new='''            fileAdapter.notifyDataSetChanged();
            updateListHeightSmart();
            try{list.setFastScrollEnabled(visibleNodes.size()>100);}catch(Throwable e){BiggerApp.logNonFatal(MainActivity.this,"FILE_MANAGER","Fast scroll",e);}
            count.setText(visibleNodes.size()+" itens • "+selected.size()+" selecionados");'''
if old not in s:
    raise SystemExit("render block não encontrado")
s=s.replace(old,new,1)

# Initial list should not reserve blank area before first render.
old2='''            int h=Math.max(dp(190),Math.min(dp(340),getResources().getDisplayMetrics().heightPixels/3));
            view.addView(list,new LinearLayout.LayoutParams(-1,h));'''
new2='''            list.setVisibility(View.GONE);
            view.addView(list,new LinearLayout.LayoutParams(-1,0));'''
if old2 not in s:
    raise SystemExit("initial list height block não encontrado")
s=s.replace(old2,new2,1)

p.write_text(s)

b=Path("buildsrc/app/build.gradle")
g=b.read_text().replace('versionCode 19','versionCode 20').replace("versionName '7.4.0'","versionName '7.5.0'")
b.write_text(g)
