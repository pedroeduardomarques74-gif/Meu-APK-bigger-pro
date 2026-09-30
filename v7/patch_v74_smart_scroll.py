from pathlib import Path

p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java")
s=p.read_text()

# Campo de gesto por Pane
old='''        int loadGeneration=0;'''
new='''        int loadGeneration=0;
        float listTouchLastY=Float.NaN;'''
if old not in s:
    raise SystemExit("campo Pane não encontrado")
s=s.replace(old,new,1)

# Substitui listener v7.3 por handoff direcional inteligente
start=s.find('''            list.setOnTouchListener((v,event)->{''')
end=s.find('''            fileAdapter=new BaseAdapter(){''',start)
if start<0 or end<0:
    raise SystemExit("listener de scroll v7.3 não encontrado")

listener=r'''            list.setOnTouchListener((v,event)->{
                try{
                    int action=event.getActionMasked();

                    if(action==android.view.MotionEvent.ACTION_DOWN){
                        listTouchLastY=event.getY();

                        // Se a lista nem tem conteúdo suficiente para rolar,
                        // não bloqueia o ScrollView pai em nenhum momento.
                        boolean scrollable=list.canScrollVertically(-1)||list.canScrollVertically(1);
                        if(!scrollable){
                            android.view.ViewParent parent=list.getParent();
                            while(parent!=null){
                                parent.requestDisallowInterceptTouchEvent(false);
                                parent=parent.getParent();
                            }
                        }
                    }else if(action==android.view.MotionEvent.ACTION_MOVE){
                        float y=event.getY();
                        float dy=Float.isNaN(listTouchLastY)?0f:(y-listTouchLastY);
                        listTouchLastY=y;

                        boolean fingerUp=dy<0f;   // usuário arrasta para cima -> quer descer na lista
                        boolean fingerDown=dy>0f; // usuário arrasta para baixo -> quer subir na lista

                        boolean childCanHandle;
                        if(fingerUp){
                            childCanHandle=list.canScrollVertically(1);
                        }else if(fingerDown){
                            childCanHandle=list.canScrollVertically(-1);
                        }else{
                            childCanHandle=list.canScrollVertically(-1)||list.canScrollVertically(1);
                        }

                        android.view.ViewParent parent=list.getParent();
                        while(parent!=null){
                            // Enquanto a lista ainda consegue andar na direção do gesto,
                            // ela recebe o movimento. Ao chegar no limite, devolve ao pai.
                            parent.requestDisallowInterceptTouchEvent(childCanHandle);
                            parent=parent.getParent();
                        }
                    }else if(action==android.view.MotionEvent.ACTION_UP ||
                             action==android.view.MotionEvent.ACTION_CANCEL){
                        listTouchLastY=Float.NaN;
                        android.view.ViewParent parent=list.getParent();
                        while(parent!=null){
                            parent.requestDisallowInterceptTouchEvent(false);
                            parent=parent.getParent();
                        }
                    }
                }catch(Throwable e){
                    BiggerApp.logNonFatal(MainActivity.this,"FILE_MANAGER","Scroll inteligente da lista",e);
                    try{
                        android.view.ViewParent parent=list.getParent();
                        while(parent!=null){
                            parent.requestDisallowInterceptTouchEvent(false);
                            parent=parent.getParent();
                        }
                    }catch(Throwable ignored){}
                }
                return false;
            });
'''
s=s[:start]+listener+s[end:]

p.write_text(s)

b=Path("buildsrc/app/build.gradle")
g=b.read_text().replace('versionCode 18','versionCode 19').replace("versionName '7.3.0'","versionName '7.4.0'")
b.write_text(g)
