from pathlib import Path

p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/AppsActivity.java")
s=p.read_text()

# Estado/lifecycle/operação
s=s.replace('''    boolean showSystem=false; volatile boolean loading=false;
    static final int REQ_SAVE_APP_FOLDER = 7611;''','''    boolean showSystem=false; volatile boolean loading=false;
    volatile boolean destroyed=false, operationBusy=false;
    ProgressDialog activeProgress;
    static final int REQ_SAVE_APP_FOLDER = 7611;''',1)

s=s.replace('''    @Override protected void onDestroy(){io.shutdownNow(); super.onDestroy();}''','''    @Override protected void onDestroy(){
        destroyed=true;
        try{if(activeProgress!=null&&activeProgress.isShowing())activeProgress.dismiss();}catch(Throwable e){BiggerApp.logNonFatal(this,"APK_EXTRACT","dismiss onDestroy",e);}
        io.shutdownNow();
        super.onDestroy();
    }''',1)

# Helpers
marker='    void build(){'
helpers=r'''    boolean alive(){
        if(destroyed||isFinishing())return false;
        return Build.VERSION.SDK_INT<17||!isDestroyed();
    }
    void safeUi(Runnable r){
        runOnUiThread(()->{if(!alive())return;try{r.run();}catch(Throwable e){BiggerApp.logNonFatal(this,"CRASH","AppsActivity UI",e);}});
    }
    void safeDismiss(ProgressDialog d){try{if(d!=null&&d.isShowing())d.dismiss();}catch(Throwable e){BiggerApp.logNonFatal(this,"APK_EXTRACT","dismiss",e);}}
    String safePrefString(String key){
        try{
            android.content.SharedPreferences sp=getSharedPreferences("bigger_otg",MODE_PRIVATE);
            Object raw=sp.getAll().get(key);
            if(raw==null)return null;
            if(raw instanceof String)return (String)raw;
            sp.edit().remove(key).apply();
        }catch(Throwable e){BiggerApp.logNonFatal(this,"STORAGE","Preferência inválida: "+key,e);}
        return null;
    }
    boolean hasPersisted(Uri u,boolean write){
        try{
            for(UriPermission p:getContentResolver().getPersistedUriPermissions())
                if(p.getUri().equals(u)&&p.isReadPermission()&&(!write||p.isWritePermission()))return true;
        }catch(Throwable e){BiggerApp.logNonFatal(this,"PERMISSION","URI persistida",e);}
        return false;
    }
    String safeName(String s){
        String n=s==null?"app":s.replaceAll("[\\\\/:*?\"<>|]","_").replaceAll("[^a-zA-Z0-9._ ()-]","_").trim();
        if(n.isEmpty())n="app";
        if(n.length()>140)n=n.substring(0,140);
        return n;
    }
    File uniqueFile(File dir,String name){
        File f=new File(dir,name);if(!f.exists())return f;
        String base=name,ext="";int dot=name.lastIndexOf('.');
        if(dot>0){base=name.substring(0,dot);ext=name.substring(dot);}
        for(int i=2;i<10000;i++){f=new File(dir,base+" ("+i+")"+ext);if(!f.exists())return f;}
        return new File(dir,base+"-"+System.currentTimeMillis()+ext);
    }

'''
s=s.replace(marker,helpers+marker,1)

# Load apps com finally e logging
start=s.find('    void loadAppsAsync(){')
end=s.find('\n    void filterList(){',start)
if start<0 or end<0: raise SystemExit("loadAppsAsync")
newload=r'''    void loadAppsAsync(){
        if(loading)return; loading=true;
        if(status!=null)status.setText("Carregando aplicativos...");
        io.execute(()->{
            ArrayList<AppItem> temp=new ArrayList<>(); Throwable fatal=null;
            try{
                PackageManager pm=getPackageManager();
                for(ApplicationInfo ai:pm.getInstalledApplications(PackageManager.GET_META_DATA)){
                    try{
                        if(ai==null||ai.packageName==null)continue;
                        AppItem x=new AppItem();x.pkg=ai.packageName;
                        CharSequence label=pm.getApplicationLabel(ai);x.name=label==null?ai.packageName:label.toString();
                        x.system=(ai.flags&ApplicationInfo.FLAG_SYSTEM)!=0;
                        PackageInfo pi=pm.getPackageInfo(ai.packageName,0);x.version=pi.versionName==null?"—":pi.versionName;
                        x.base=ai.sourceDir;
                        ArrayList<String> splits=new ArrayList<>();
                        if(ai.splitSourceDirs!=null)for(String sp:ai.splitSourceDirs)if(sp!=null&&!sp.trim().isEmpty())splits.add(sp);
                        x.splits=splits.toArray(new String[0]);
                        x.size=size(x.base);for(String sp:x.splits)x.size+=size(sp);
                        if(x.base!=null&&!x.base.trim().isEmpty())temp.add(x);
                    }catch(Throwable e){BiggerApp.logNonFatal(this,"APK_EXTRACT","Falha ao ler app instalado",e);}
                }
                Collections.sort(temp,(a,b)->String.valueOf(a.name).compareToIgnoreCase(String.valueOf(b.name)));
            }catch(Throwable e){fatal=e;BiggerApp.logNonFatal(this,"APK_EXTRACT","Falha ao listar apps",e);}
            Throwable err=fatal;
            safeUi(()->{
                loading=false;all.clear();all.addAll(temp);
                status.setText(err==null?all.size()+" aplicativos encontrados":"Não foi possível listar todos os aplicativos");
                filterList();
            });
        });
    }

'''
s=s[:start]+newload+s[end:]

# Diálogos só com Activity válida
s=s.replace('''    void menu(AppItem a){
        ArrayList<String> o=new ArrayList<>();o.add("Extrair APK");o.add("Extrair e escolher pasta no celular");if(a.splits.length>0)o.add("Backup completo (base + splits)");o.add("Extrair e enviar ao USB");o.add("Detalhes");
        new AlertDialog.Builder(this).setTitle(a.name).setItems(o.toArray(new String[0]),(d,w)->{String s=o.get(w);if(s.equals("Extrair APK"))extractMany(Collections.singletonList(a),false,false);else if(s.equals("Extrair e escolher pasta no celular"))chooseSaveFolder(a);else if(s.startsWith("Backup"))extractMany(Collections.singletonList(a),false,true);else if(s.startsWith("Extrair e enviar"))extractMany(Collections.singletonList(a),true,true);else details(a);}).show();
    }''','''    void menu(AppItem a){
        if(!alive()||a==null)return;
        ArrayList<String> o=new ArrayList<>();o.add("Extrair APK");o.add("Extrair e escolher pasta no celular");if(a.splits.length>0)o.add("Backup completo (base + splits)");o.add("Extrair e enviar ao USB");o.add("Detalhes");
        try{new AlertDialog.Builder(this).setTitle(a.name).setItems(o.toArray(new String[0]),(d,w)->{String v=o.get(w);if(v.equals("Extrair APK"))extractMany(Collections.singletonList(a),false,false);else if(v.equals("Extrair e escolher pasta no celular"))chooseSaveFolder(a);else if(v.startsWith("Backup"))extractMany(Collections.singletonList(a),false,true);else if(v.startsWith("Extrair e enviar"))extractMany(Collections.singletonList(a),true,true);else details(a);}).show();}
        catch(Throwable e){BiggerApp.logNonFatal(this,"APK_EXTRACT","Abrir menu",e);}
    }''',1)

# escolher pasta seguro
s=s.replace('''        startActivityForResult(i, REQ_SAVE_APP_FOLDER);''','''        try{startActivityForResult(i, REQ_SAVE_APP_FOLDER);}
        catch(Throwable e){pendingSaveApp=null;BiggerApp.logNonFatal(this,"STORAGE","Abrir seletor de pasta",e);toast("Não foi possível abrir o seletor de pasta.");}''',1)

# save chosen lifecycle
s=s.replace('''        ProgressDialog pd=new ProgressDialog(this);
        pd.setTitle("Salvando APK");''','''        if(operationBusy){toast("Já existe uma operação em andamento.");return;}
        operationBusy=true; BiggerApp.markAction(this,"SAVE_APK_TO_PHONE");
        ProgressDialog pd=new ProgressDialog(this); activeProgress=pd;
        pd.setTitle("Salvando APK");''',1)
s=s.replace('''        pd.show();

        io.execute(()->{''','''        try{pd.show();}catch(Throwable e){operationBusy=false;BiggerApp.logNonFatal(this,"APK_EXTRACT","Mostrar progresso",e);return;}

        io.execute(()->{''',1)
s=s.replace('''            runOnUiThread(()->{
                pd.dismiss();
                if(done) toast(app.splits.length==0 ? app.name+".apk salvo na pasta escolhida." : "Backup completo de "+app.name+" salvo na pasta escolhida.");
                else new AlertDialog.Builder(this).setTitle("Não foi possível salvar").setMessage(msg==null?"O Android não liberou a gravação nessa pasta.":msg).setPositiveButton("OK",null).show();
            });''','''            safeUi(()->{
                operationBusy=false;activeProgress=null;safeDismiss(pd);
                if(done) toast(app.splits.length==0 ? app.name+".apk salvo na pasta escolhida." : "Backup completo de "+app.name+" salvo na pasta escolhida.");
                else try{new AlertDialog.Builder(this).setTitle("Não foi possível salvar").setMessage(msg==null?"O Android não liberou a gravação nessa pasta.":msg).setPositiveButton("OK",null).show();}
                catch(Throwable e){BiggerApp.logNonFatal(this,"APK_EXTRACT","Mostrar erro de salvamento",e);}
            });''',1)

# save file validation / buffered IO
s=s.replace('''    void saveSourceFileToTree(File source,Uri parent,String displayName)throws Exception{
        Uri dest=DocumentsContract.createDocument(
            getContentResolver(),
            parent,
            "application/vnd.android.package-archive",
            displayName
        );
        if(dest==null) throw new IOException("Falha ao criar "+displayName);
        try(InputStream in=new FileInputStream(source);OutputStream out=getContentResolver().openOutputStream(dest,"w")){
            if(out==null) throw new IOException("Falha ao abrir o destino");
            byte[] buf=new byte[262144];
            int r;
            while((r=in.read(buf))>0) out.write(buf,0,r);
            out.flush();
        }
    }''','''    void saveSourceFileToTree(File source,Uri parent,String displayName)throws Exception{
        if(source==null||!source.exists()||!source.isFile()||!source.canRead())throw new FileNotFoundException("APK de origem indisponível");
        Uri dest=DocumentsContract.createDocument(getContentResolver(),parent,"application/vnd.android.package-archive",safeName(displayName));
        if(dest==null) throw new IOException("Falha ao criar "+displayName);
        try(InputStream in=new BufferedInputStream(new FileInputStream(source));OutputStream raw=getContentResolver().openOutputStream(dest,"w")){
            if(raw==null) throw new IOException("Falha ao abrir o destino");
            try(OutputStream out=new BufferedOutputStream(raw)){
                byte[] buf=new byte[128*1024];int r;while((r=in.read(buf))>0)out.write(buf,0,r);out.flush();
            }
        }catch(Throwable e){
            try{DocumentsContract.deleteDocument(getContentResolver(),dest);}catch(Throwable ignored){}
            if(e instanceof Exception)throw (Exception)e;
            throw new IOException(e);
        }
    }''',1)

# extractMany robusto
start=s.find('    void extractMany(List<AppItem> src,boolean toUsb,boolean full){')
end=s.find('\n    List<File> extract(',start)
if start<0 or end<0: raise SystemExit("extractMany")
newextractmany=r'''    void extractMany(List<AppItem> src,boolean toUsb,boolean full){
        if(operationBusy){toast("Já existe uma extração em andamento.");return;}
        if(src==null||src.isEmpty()){toast("Selecione pelo menos um aplicativo.");return;}
        Uri usb=toUsb?savedUsb():null;
        if(toUsb&&usb==null){toast("USB indisponível ou permissão revogada. Autorize novamente.");return;}
        operationBusy=true; BiggerApp.markAction(this,toUsb?"EXTRACT_APK_USB":"EXTRACT_APK");
        ProgressDialog pd=new ProgressDialog(this);activeProgress=pd;pd.setTitle(toUsb?"Extraindo e enviando ao USB":"Extraindo APKs");pd.setProgressStyle(ProgressDialog.STYLE_HORIZONTAL);pd.setMax(src.size());pd.setCancelable(false);
        try{pd.show();}catch(Throwable e){operationBusy=false;activeProgress=null;BiggerApp.logNonFatal(this,"APK_EXTRACT","Mostrar progresso",e);return;}
        io.execute(()->{
            ArrayList<String> paths=new ArrayList<>();int ok=0;int failed=0;String lastError=null;
            for(int i=0;i<src.size();i++){
                AppItem a=src.get(i);final int n=i;
                safeUi(()->{if(pd.isShowing()){pd.setMessage(a.name);pd.setProgress(n);}});
                try{
                    List<File> out=extract(a,full);
                    if(out.isEmpty())throw new IOException("Nenhum APK gerado");
                    boolean appOk=true;
                    for(File f:out){
                        if(f==null||!f.exists()||f.length()<=0){appOk=false;continue;}
                        paths.add(f.getAbsolutePath());
                        if(toUsb)copyToUsb(f,usb);
                    }
                    if(appOk)ok++;else failed++;
                }catch(Throwable e){failed++;lastError=e.getMessage();BiggerApp.logNonFatal(this,"APK_EXTRACT","Falha ao extrair "+(a==null?"?":a.pkg),e);}
            }
            int good=ok,bad=failed;String err=lastError;
            safeUi(()->{
                operationBusy=false;activeProgress=null;safeDismiss(pd);selected.clear();selectedLabel.setText("0 selecionados");adapter.notifyDataSetChanged();
                toast(good+" de "+src.size()+" aplicativo(s) extraído(s)."+(bad>0?" Houve "+bad+" falha(s).":""));
                if(!paths.isEmpty())openInBigger(paths);
                else if(err!=null)toast("Falha: "+err);
            });
        });
    }

'''
s=s[:start]+newextractmany+s[end:]

# extract único/seguro/sem sobrescrever
start=s.find('    List<File> extract(AppItem a,boolean full)throws Exception{')
end=s.find('\n    Uri savedUsb()',start)
newextract=r'''    List<File> extract(AppItem a,boolean full)throws Exception{
        if(a==null||a.base==null)throw new FileNotFoundException("Aplicativo sem APK base");
        File base=new File(a.base);if(!base.exists()||!base.isFile()||!base.canRead())throw new FileNotFoundException("APK base indisponível");
        File root=new File(getCacheDir(),"extracted_apks");if(!root.exists()&&!root.mkdirs())throw new IOException("Falha ao preparar cache");
        if(root.getUsableSpace()>0&&root.getUsableSpace()<Math.max(a.size,5*1024*1024L))throw new IOException("Espaço insuficiente");
        ArrayList<File> out=new ArrayList<>();String n=safeName(a.name),v=safeName(a.version);
        if(a.splits==null)a.splits=new String[0];
        if(a.splits.length==0||!full){File d=uniqueFile(root,n+".apk");copy(base,d);out.add(d);return out;}
        File dir=uniqueFile(root,n+"_"+v+"_SPLIT");if(!dir.mkdirs())throw new IOException("Falha ao criar pasta do split");
        File b=new File(dir,n+"_base.apk");copy(base,b);out.add(b);
        for(int i=0;i<a.splits.length;i++){
            String sp=a.splits[i];if(sp==null)continue;File src=new File(sp);if(!src.exists()||!src.canRead())throw new FileNotFoundException("Split indisponível");
            String nm=safeName(src.getName().toLowerCase(Locale.ROOT).endsWith(".apk")?src.getName():"split_"+(i+1)+".apk");
            File d=uniqueFile(dir,nm);copy(src,d);out.add(d);
        }
        return out;
    }

'''
s=s[:start]+newextract+s[end:]

# USB pref/permission e copy
start=s.find('    Uri savedUsb(){')
end=s.find('\n    void openInBigger',start)
newusb=r'''    Uri savedUsb(){
        String raw=safePrefString("usb");if(raw==null)return null;
        try{
            Uri u=Uri.parse(raw);
            if(!"content".equalsIgnoreCase(u.getScheme())||!DocumentsContract.isTreeUri(u)||!hasPersisted(u,true))return null;
            DocumentsContract.getTreeDocumentId(u);return u;
        }catch(Throwable e){BiggerApp.logNonFatal(this,"USB_OTG","USB salvo inválido",e);return null;}
    }
    void copyToUsb(File f,Uri tree)throws Exception{
        if(f==null||!f.exists()||!f.canRead())throw new FileNotFoundException("Arquivo de origem indisponível");
        if(tree==null||!hasPersisted(tree,true))throw new SecurityException("Permissão USB perdida");
        String rootId=DocumentsContract.getTreeDocumentId(tree);Uri parent=DocumentsContract.buildDocumentUriUsingTree(tree,rootId);
        String name=safeName(f.getName());Uri dest=DocumentsContract.createDocument(getContentResolver(),parent,"application/vnd.android.package-archive",name);
        if(dest==null)throw new IOException("Não foi possível criar arquivo no USB");
        try(InputStream in=new BufferedInputStream(new FileInputStream(f));OutputStream raw=getContentResolver().openOutputStream(dest,"w")){
            if(raw==null)throw new IOException("USB indisponível");
            try(OutputStream out=new BufferedOutputStream(raw)){byte[] b=new byte[128*1024];int r;while((r=in.read(b))>0)out.write(b,0,r);out.flush();}
        }catch(Throwable e){
            try{DocumentsContract.deleteDocument(getContentResolver(),dest);}catch(Throwable ignored){}
            if(e instanceof Exception)throw (Exception)e;throw new IOException(e);
        }
    }
'''
s=s[:start]+newusb+s[end:]

# buffered copy
s=s.replace('''    void copy(File a,File b)throws Exception{try(InputStream in=new FileInputStream(a);OutputStream out=new FileOutputStream(b)){byte[] x=new byte[262144];int r;while((r=in.read(x))>0)out.write(x,0,r);}}''','''    void copy(File a,File b)throws Exception{
        if(a==null||!a.exists()||!a.isFile()||!a.canRead())throw new FileNotFoundException("Origem inválida");
        try(InputStream in=new BufferedInputStream(new FileInputStream(a));OutputStream out=new BufferedOutputStream(new FileOutputStream(b))){
            byte[] x=new byte[128*1024];int r;while((r=in.read(x))>0)out.write(x,0,r);out.flush();
        }catch(Throwable e){try{if(b!=null)b.delete();}catch(Throwable ignored){}if(e instanceof Exception)throw (Exception)e;throw new IOException(e);}
        if(!b.exists()||b.length()<=0)throw new IOException("Arquivo extraído vazio");
    }''',1)

# substitui safe antigo para não conflitar
s=s.replace('''    String safe(String s){return s==null?"app":s.replaceAll("[^a-zA-Z0-9._ -]","_").trim();}''','''    String safe(String s){return safeName(s);}''',1)

p.write_text(s)
