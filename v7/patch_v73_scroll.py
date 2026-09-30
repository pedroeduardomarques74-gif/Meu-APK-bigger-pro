from pathlib import Path

p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java")
s=p.read_text()

old='''            list=new ListView(MainActivity.this); list.setDividerHeight(dp(4)); list.setClipToPadding(false);
            fileAdapter=new BaseAdapter(){'''
new='''            list=new ListView(MainActivity.this);
            list.setDividerHeight(dp(4));
            list.setClipToPadding(false);
            list.setVerticalScrollBarEnabled(true);
            list.setScrollbarFadingEnabled(false);
            list.setFastScrollEnabled(currentNodes.size()>100);
            if(Build.VERSION.SDK_INT>=21) list.setNestedScrollingEnabled(true);
            list.setOnTouchListener((v,event)->{
                try{
                    int action=event.getActionMasked();
                    if(action==android.view.MotionEvent.ACTION_DOWN || action==android.view.MotionEvent.ACTION_MOVE){
                        // A lista CELULAR/USB deve receber o gesto quando há conteúdo para rolar.
                        boolean canUp=list.canScrollVertically(-1);
                        boolean canDown=list.canScrollVertically(1);
                        if(canUp||canDown){
                            android.view.ViewParent parent=list.getParent();
                            while(parent!=null){
                                parent.requestDisallowInterceptTouchEvent(true);
                                parent=parent.getParent();
                            }
                        }
                    }else if(action==android.view.MotionEvent.ACTION_UP || action==android.view.MotionEvent.ACTION_CANCEL){
                        android.view.ViewParent parent=list.getParent();
                        while(parent!=null){
                            parent.requestDisallowInterceptTouchEvent(false);
                            parent=parent.getParent();
                        }
                    }
                }catch(Throwable e){
                    BiggerApp.logNonFatal(MainActivity.this,"FILE_MANAGER","Controle de scroll da lista",e);
                }
                return false;
            });
            fileAdapter=new BaseAdapter(){'''
if old not in s:
    raise SystemExit("ListView init não encontrado")
s=s.replace(old,new,1)

# Atualiza fast-scroll conforme quantidade atual
old2='''            fileAdapter.notifyDataSetChanged();
            count.setText(visibleNodes.size()+" itens • "+selected.size()+" selecionados");'''
new2='''            fileAdapter.notifyDataSetChanged();
            try{list.setFastScrollEnabled(visibleNodes.size()>100);}catch(Throwable e){BiggerApp.logNonFatal(MainActivity.this,"FILE_MANAGER","Fast scroll",e);}
            count.setText(visibleNodes.size()+" itens • "+selected.size()+" selecionados");'''
if old2 not in s:
    raise SystemExit("render marker não encontrado")
s=s.replace(old2,new2,1)

p.write_text(s)

b=Path("buildsrc/app/build.gradle")
g=b.read_text().replace('versionCode 17','versionCode 18').replace("versionName '7.2.0'","versionName '7.3.0'")
b.write_text(g)
