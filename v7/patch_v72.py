from pathlib import Path

Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/ShareFileProvider.java").write_text(
    Path("v7/ShareFileProvider.java").read_text()
)

p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/AppsActivity.java")
s=p.read_text()

s=s.replace(
'''    static final int REQ_SAVE_APP_FOLDER = 7611;
    AppItem pendingSaveApp = null;''',
'''    static final int REQ_SAVE_APP_FOLDER = 7611;
    static final String SAVE_SIMPLE="simple", SAVE_SPLIT_FOLDER="split_folder", SAVE_SPLIT_ZIP="split_zip";
    AppItem pendingSaveApp = null;
    String pendingSaveMode = SAVE_SIMPLE;''',1)

start=s.find('    void menu(AppItem a){')
end=s.find('\n    void details(AppItem a)',start)
if start<0 or end<0: raise SystemExit("menu não encontrado")
new_menu=r'''    void menu(AppItem a){
        if(!alive()||a==null)return;
        ArrayList<String> o=new ArrayList<>();
        o.add("Extrair APK");
        if(a.splits!=null && a.splits.length>0){
            o.add("Salvar split no celular");
            o.add("Compartilhar split");
            o.add("Backup completo (base + splits)");
        }else{
            o.add("Extrair e escolher pasta no celular");
            o.add("Compartilhar APK");
        }
        o.add("Extrair e enviar ao USB");
        o.add("Detalhes");
        try{
            new AlertDialog.Builder(this).setTitle(a.name).setItems(o.toArray(new String[0]),(d,w)->{
                String v=o.get(w);
                if(v.equals("Extrair APK"))extractMany(Collections.singletonList(a),false,false);
                else if(v.equals("Extrair e escolher pasta no celular"))chooseSaveFolder(a,SAVE_SIMPLE);
                else if(v.equals("Salvar split no celular"))showSplitSaveOptions(a);
                else if(v.equals("Compartilhar split"))showSplitShareOptions(a);
                else if(v.equals("Compartilhar APK"))prepareAndShare(a,false,false);
                else if(v.startsWith("Backup"))extractMany(Collections.singletonList(a),false,true);
                else if(v.startsWith("Extrair e enviar"))extractMany(Collections.singletonList(a),true,true);
                else details(a);
            }).show();
        }catch(Throwable e){BiggerApp.logNonFatal(this,"APK_EXTRACT","Abrir menu",e);}
    }

    void showSplitSaveOptions(AppItem app){
        if(!alive()||app==null)return;
        String[] opts={"📁 Pasta normal (base + splits)","🗜️ Arquivo ZIP"};
        try{
            new AlertDialog.Builder(this)
                .setTitle("Salvar "+app.name)
                .setItems(opts,(d,which)->{
                    if(which==0)chooseSaveFolder(app,SAVE_SPLIT_FOLDER);
                    else chooseSaveFolder(app,SAVE_SPLIT_ZIP);
                }).show();
        }catch(Throwable e){BiggerApp.logNonFatal(this,"APK_EXTRACT","Opções de salvar split",e);}
    }

    void showSplitShareOptions(AppItem app){
        if(!alive()||app==null)return;
        String[] opts={"🗜️ Compartilhar ZIP único","📦 Compartilhar APKs separados"};
        try{
            new AlertDialog.Builder(this)
                .setTitle("Compartilhar "+app.name)
                .setItems(opts,(d,which)->{
                    if(which==0)prepareAndShare(app,true,false);
                    else prepareAndShare(app,false,true);
                }).show();
        }catch(Throwable e){BiggerApp.logNonFatal(this,"APK_EXTRACT","Opções de compartilhar split",e);}
    }

'''
s=s[:start]+new_menu+s[end:]

start=s.find('    void chooseSaveFolder(AppItem app) {')
end=s.find('\n    @Override protected void onActivityResult',start)
if start<0 or end<0: raise SystemExit("chooseSaveFolder não encontrado")
new_choose=r'''    void chooseSaveFolder(AppItem app,String mode) {
        pendingSaveApp = app;
        pendingSaveMode = mode==null?SAVE_SIMPLE:mode;
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION |
                   Intent.FLAG_GRANT_WRITE_URI_PERMISSION |
                   Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION |
                   Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
        try{startActivityForResult(i, REQ_SAVE_APP_FOLDER);}
        catch(Throwable e){
            pendingSaveApp=null;pendingSaveMode=SAVE_SIMPLE;
            BiggerApp.logNonFatal(this,"STORAGE","Abrir seletor de pasta",e);
            toast("Não foi possível abrir o seletor de pasta.");
        }
    }

'''
s=s[:start]+new_choose+s[end:]

s=s.replace(
'''        AppItem app = pendingSaveApp;
        pendingSaveApp = null;
        saveInstalledAppToChosenFolder(app, tree);''',
'''        AppItem app = pendingSaveApp;
        String mode = pendingSaveMode;
        pendingSaveApp = null;
        pendingSaveMode = SAVE_SIMPLE;
        saveInstalledAppToChosenFolder(app, tree, mode);''',1)

start=s.find('    void saveInstalledAppToChosenFolder(AppItem app,Uri tree) {')
end=s.find('\n    void saveSourceFileToTree',start)
if start<0 or end<0: raise SystemExit("saveInstalledAppToChosenFolder não encontrado")
new_save=r'''    void saveInstalledAppToChosenFolder(AppItem app,Uri tree,String mode) {
        if(operationBusy){toast("Já existe uma operação em andamento.");return;}
        if(app==null||tree==null){toast("Destino inválido.");return;}
        operationBusy=true; BiggerApp.markAction(this,"SAVE_APK_TO_PHONE");
        ProgressDialog pd=new ProgressDialog(this); activeProgress=pd;
        pd.setTitle("Salvando");
        pd.setMessage(app.name);
        pd.setIndeterminate(true);
        pd.setCancelable(false);
        try{pd.show();}catch(Throwable e){operationBusy=false;activeProgress=null;BiggerApp.logNonFatal(this,"APK_EXTRACT","Mostrar progresso",e);return;}

        io.execute(()->{
            boolean ok=false; String error=null; String success=null;
            try {
                String rootId=DocumentsContract.getTreeDocumentId(tree);
                Uri targetParent=DocumentsContract.buildDocumentUriUsingTree(tree,rootId);

                if(SAVE_SPLIT_ZIP.equals(mode)){
                    File zip=createSplitZip(app);
                    saveAnyFileToTree(zip,targetParent,zip.getName(),"application/zip");
                    success=zip.getName()+" salvo na pasta escolhida.";
                }else if(SAVE_SPLIT_FOLDER.equals(mode)){
                    saveSplitFolderToTree(app,targetParent);
                    success="Split de "+app.name+" salvo em pasta normal.";
                }else if(app.splits==null||app.splits.length==0){
                    saveSourceFileToTree(new File(app.base),targetParent,safe(app.name)+".apk");
                    success=app.name+".apk salvo na pasta escolhida.";
                }else{
                    saveSplitFolderToTree(app,targetParent);
                    success="Backup completo de "+app.name+" salvo na pasta escolhida.";
                }
                ok=true;
            } catch(Throwable e) {
                error=e.getMessage();
                BiggerApp.logNonFatal(this,"APK_EXTRACT","Salvar no celular",e);
            }
            boolean done=ok; String msg=error, doneMsg=success;
            safeUi(()->{
                operationBusy=false;activeProgress=null;safeDismiss(pd);
                if(done) toast(doneMsg==null?"Arquivo salvo.":doneMsg);
                else try{
                    new AlertDialog.Builder(this).setTitle("Não foi possível salvar")
                        .setMessage(msg==null?"O Android não liberou a gravação nessa pasta.":msg)
                        .setPositiveButton("OK",null).show();
                }catch(Throwable e){BiggerApp.logNonFatal(this,"APK_EXTRACT","Mostrar erro de salvamento",e);}
            });
        });
    }

    void saveSplitFolderToTree(AppItem app,Uri targetParent)throws Exception{
        Uri folder=DocumentsContract.createDocument(
            getContentResolver(),targetParent,DocumentsContract.Document.MIME_TYPE_DIR,
            safe(app.name)+"_SPLIT"
        );
        if(folder==null)throw new IOException("Não foi possível criar a pasta do split");
        saveSourceFileToTree(new File(app.base),folder,safe(app.name)+"_base.apk");
        if(app.splits!=null){
            for(int i=0;i<app.splits.length;i++){
                File src=new File(app.splits[i]);
                String name=src.getName();
                if(!name.toLowerCase(Locale.ROOT).endsWith(".apk"))name="split_"+(i+1)+".apk";
                saveSourceFileToTree(src,folder,name);
            }
        }
    }

    void saveAnyFileToTree(File source,Uri parent,String displayName,String mime)throws Exception{
        if(source==null||!source.exists()||!source.isFile()||!source.canRead())throw new FileNotFoundException("Arquivo de origem indisponível");
        Uri dest=DocumentsContract.createDocument(getContentResolver(),parent,mime,safeName(displayName));
        if(dest==null)throw new IOException("Falha ao criar "+displayName);
        try(InputStream in=new BufferedInputStream(new FileInputStream(source));OutputStream raw=getContentResolver().openOutputStream(dest,"w")){
            if(raw==null)throw new IOException("Falha ao abrir o destino");
            try(OutputStream out=new BufferedOutputStream(raw)){
                byte[] buf=new byte[128*1024];int r;while((r=in.read(buf))>0)out.write(buf,0,r);out.flush();
            }
        }catch(Throwable e){
            try{DocumentsContract.deleteDocument(getContentResolver(),dest);}catch(Throwable clean){BiggerApp.logNonFatal(this,"STORAGE","Limpar destino parcial",clean);}
            if(e instanceof Exception)throw (Exception)e;throw new IOException(e);
        }
    }

    File createSplitZip(AppItem app)throws Exception{
        if(app==null||app.base==null)throw new FileNotFoundException("Aplicativo inválido");
        File root=new File(getCacheDir(),"share_ready");
        if(!root.exists()&&!root.mkdirs())throw new IOException("Não foi possível preparar o ZIP");
        File zip=uniqueFile(root,safeName(app.name)+"_SPLIT.zip");
        try(java.util.zip.ZipOutputStream out=new java.util.zip.ZipOutputStream(new BufferedOutputStream(new FileOutputStream(zip)))){
            addFileToZip(out,new File(app.base),safeName(app.name)+"_base.apk");
            if(app.splits!=null){
                for(int i=0;i<app.splits.length;i++){
                    File f=new File(app.splits[i]);
                    String n=f.getName();
                    if(!n.toLowerCase(Locale.ROOT).endsWith(".apk"))n="split_"+(i+1)+".apk";
                    addFileToZip(out,f,safeName(n));
                }
            }
        }catch(Throwable e){
            try{zip.delete();}catch(Throwable clean){BiggerApp.logNonFatal(this,"APK_EXTRACT","Limpar ZIP parcial",clean);}
            if(e instanceof Exception)throw (Exception)e;throw new IOException(e);
        }
        if(!zip.exists()||zip.length()<=0)throw new IOException("ZIP gerado vazio");
        return zip;
    }

    void addFileToZip(java.util.zip.ZipOutputStream out,File f,String entryName)throws Exception{
        if(f==null||!f.exists()||!f.isFile()||!f.canRead())throw new FileNotFoundException("Parte do split indisponível");
        java.util.zip.ZipEntry entry=new java.util.zip.ZipEntry(entryName);
        entry.setTime(f.lastModified());
        out.putNextEntry(entry);
        try(InputStream in=new BufferedInputStream(new FileInputStream(f))){
            byte[] buf=new byte[128*1024];int r;while((r=in.read(buf))>0)out.write(buf,0,r);
        }
        out.closeEntry();
    }

'''
s=s[:start]+new_save+s[end:]

insert_at=s.find('    void extractMany(List<AppItem> src,boolean toUsb,boolean full){')
if insert_at<0: raise SystemExit("extractMany marker não encontrado")
share_methods=r'''    void prepareAndShare(AppItem app,boolean asZip,boolean separateSplits){
        if(operationBusy){toast("Já existe uma operação em andamento.");return;}
        if(app==null){toast("Aplicativo inválido.");return;}
        operationBusy=true; BiggerApp.markAction(this,"SHARE_APK");
        ProgressDialog pd=new ProgressDialog(this);activeProgress=pd;
        pd.setTitle("Preparando compartilhamento");pd.setMessage(app.name);pd.setIndeterminate(true);pd.setCancelable(false);
        try{pd.show();}catch(Throwable e){operationBusy=false;activeProgress=null;BiggerApp.logNonFatal(this,"APK_EXTRACT","Mostrar progresso de compartilhar",e);return;}

        io.execute(()->{
            try{
                if(asZip){
                    File zip=createSplitZip(app);
                    safeUi(()->shareFiles(Collections.singletonList(zip),true));
                }else if(separateSplits){
                    List<File> files=extract(app,true);
                    safeUi(()->shareFiles(files,false));
                }else{
                    List<File> files=extract(app,false);
                    safeUi(()->shareFiles(files,false));
                }
            }catch(Throwable e){
                BiggerApp.logNonFatal(this,"APK_EXTRACT","Preparar compartilhamento",e);
                safeUi(()->toast("Não foi possível preparar o compartilhamento."));
            }finally{
                safeUi(()->{operationBusy=false;activeProgress=null;safeDismiss(pd);});
            }
        });
    }

    void shareFiles(List<File> files,boolean zipMode){
        if(!alive()||files==null||files.isEmpty())return;
        try{
            ArrayList<Uri> uris=new ArrayList<>();
            for(File f:files){
                if(f!=null&&f.exists()&&f.isFile()&&f.length()>0)uris.add(ShareFileProvider.uriFor(this,f));
            }
            if(uris.isEmpty())throw new FileNotFoundException("Nenhum arquivo pronto para compartilhar");

            Intent send;
            if(uris.size()==1){
                send=new Intent(Intent.ACTION_SEND);
                send.putExtra(Intent.EXTRA_STREAM,uris.get(0));
            }else{
                send=new Intent(Intent.ACTION_SEND_MULTIPLE);
                send.putParcelableArrayListExtra(Intent.EXTRA_STREAM,uris);
            }
            send.setType(zipMode?"application/zip":"application/vnd.android.package-archive");
            send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);

            ClipData clip=ClipData.newUri(getContentResolver(),files.get(0).getName(),uris.get(0));
            for(int i=1;i<uris.size();i++)clip.addItem(new ClipData.Item(uris.get(i)));
            send.setClipData(clip);

            startActivity(Intent.createChooser(send,"Compartilhar com..."));
        }catch(ActivityNotFoundException e){
            BiggerApp.logNonFatal(this,"SHARE_INTENT","Nenhum app para compartilhar",e);
            toast("Nenhum aplicativo disponível para compartilhar.");
        }catch(Throwable e){
            BiggerApp.logNonFatal(this,"SHARE_INTENT","Compartilhar APK/ZIP",e);
            toast("Falha ao abrir o compartilhamento.");
        }
    }

'''
s=s[:insert_at]+share_methods+s[insert_at:]
p.write_text(s)

m=Path("buildsrc/app/src/main/AndroidManifest.xml")
ms=m.read_text()
provider='''        <provider
            android:name=".ShareFileProvider"
            android:authorities="\${applicationId}.sharefiles"
            android:exported="false"
            android:grantUriPermissions="true" />
'''
if '.ShareFileProvider' not in ms:
    ms=ms.replace('<activity android:name=".AppsActivity"',provider+'        <activity android:name=".AppsActivity"',1)
m.write_text(ms)

b=Path("buildsrc/app/build.gradle")
g=b.read_text().replace('versionCode 16','versionCode 17').replace("versionName '7.1.0'","versionName '7.2.0'")
b.write_text(g)
