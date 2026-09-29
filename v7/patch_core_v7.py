from pathlib import Path
import re

m=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java")
s=m.read_text()

# Estado de ciclo de vida / operação
s=s.replace('''    boolean wizardVisible = false;
    boolean receiverRegistered = false;''','''    boolean wizardVisible = false;
    boolean receiverRegistered = false;
    volatile boolean destroyed = false;
    volatile boolean transferBusy = false;''',1)

# onCreate: não restaurar roots antes dos Panes existirem + prefs seguras
s=s.replace('''        registerUsbReceiver();
        restoreRoots();
        refreshUsbStatus();
        if (prefs.getBoolean("setup_done", false)) showMainUi(); else showSetupWizard();''','''        registerUsbReceiver();
        refreshUsbStatus();
        if (safePrefBoolean("setup_done", false)) showMainUi(); else showSetupWizard();''',1)

# onDestroy robusto
s=s.replace('''    @Override protected void onDestroy() {
        if (receiverRegistered) try { unregisterReceiver(usbReceiver); } catch (Exception ignored) {}
        io.shutdownNow();
        super.onDestroy();
    }''','''    @Override protected void onDestroy() {
        destroyed = true;
        if (receiverRegistered) try { unregisterReceiver(usbReceiver); }
        catch (Throwable e) { BiggerApp.logNonFatal(this,"USB_OTG","unregisterReceiver",e); }
        io.shutdownNow();
        super.onDestroy();
    }''',1)

# Helpers centrais
marker='    void configureEdgeToEdge() {'
helpers=r'''    boolean isAliveForUi(){
        if(destroyed || isFinishing()) return false;
        return Build.VERSION.SDK_INT < 17 || !isDestroyed();
    }

    void safeUi(Runnable r){
        runOnUiThread(() -> {
            if(!isAliveForUi()) return;
            try{ r.run(); }catch(Throwable e){ BiggerApp.logNonFatal(this,"CRASH","safeUi",e); }
        });
    }

    String safePrefString(String key){
        try{
            Object raw=prefs.getAll().get(key);
            if(raw==null)return null;
            if(raw instanceof String)return (String)raw;
            prefs.edit().remove(key).apply();
            BiggerApp.logNonFatal(this,"APP_INIT","Preferencia com tipo invalido: "+key,new ClassCastException(String.valueOf(raw.getClass())));
        }catch(Throwable e){
            BiggerApp.logNonFatal(this,"APP_INIT","Falha ao ler preferencia: "+key,e);
            try{prefs.edit().remove(key).apply();}catch(Throwable ignored){}
        }
        return null;
    }

    boolean safePrefBoolean(String key,boolean def){
        try{
            Object raw=prefs.getAll().get(key);
            if(raw==null)return def;
            if(raw instanceof Boolean)return (Boolean)raw;
            prefs.edit().remove(key).apply();
            BiggerApp.logNonFatal(this,"APP_INIT","Preferencia booleana invalida: "+key,new ClassCastException(String.valueOf(raw.getClass())));
        }catch(Throwable e){
            BiggerApp.logNonFatal(this,"APP_INIT","Falha ao ler preferencia booleana: "+key,e);
            try{prefs.edit().remove(key).apply();}catch(Throwable ignored){}
        }
        return def;
    }

    Uri safeTreeUri(String key,boolean requireWrite){
        String raw=safePrefString(key);
        if(raw==null)return null;
        try{
            Uri u=Uri.parse(raw);
            if(!"content".equalsIgnoreCase(u.getScheme()) || !DocumentsContract.isTreeUri(u) || !hasPersistedPermission(u,requireWrite))
                throw new SecurityException("URI sem permissao persistida valida");
            DocumentsContract.getTreeDocumentId(u);
            return u;
        }catch(Throwable e){
            BiggerApp.logNonFatal(this,"STORAGE","URI salva invalida: "+key,e);
            try{prefs.edit().remove(key).apply();}catch(Throwable ignored){}
            return null;
        }
    }

    void putVisualCache(String key,android.graphics.drawable.Drawable d){
        if(key==null||d==null)return;
        if(fileVisualCache.size()>=96) fileVisualCache.clear();
        fileVisualCache.put(key,d);
    }

'''
s=s.replace(marker,helpers+marker,1)

# register receiver não pode derrubar abertura
old='''    void registerUsbReceiver() {
        IntentFilter f = new IntentFilter();
        f.addAction(UsbManager.ACTION_USB_DEVICE_ATTACHED);
        f.addAction(UsbManager.ACTION_USB_DEVICE_DETACHED);
        f.addAction(ACTION_USB_PERMISSION);
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(usbReceiver, f, Context.RECEIVER_NOT_EXPORTED);
        else registerReceiver(usbReceiver, f);
        receiverRegistered = true;
    }'''
new='''    void registerUsbReceiver() {
        try{
            IntentFilter f = new IntentFilter();
            f.addAction(UsbManager.ACTION_USB_DEVICE_ATTACHED);
            f.addAction(UsbManager.ACTION_USB_DEVICE_DETACHED);
            f.addAction(ACTION_USB_PERMISSION);
            if (Build.VERSION.SDK_INT >= 33) registerReceiver(usbReceiver, f, Context.RECEIVER_NOT_EXPORTED);
            else registerReceiver(usbReceiver, f);
            receiverRegistered = true;
        }catch(Throwable e){
            receiverRegistered=false;
            BiggerApp.logNonFatal(this,"USB_OTG","Falha ao registrar receiver USB",e);
        }
    }'''
if old not in s: raise SystemExit("registerUsbReceiver não encontrado")
s=s.replace(old,new,1)

# SAF dispensa acesso total ao armazenamento
start=s.find('    boolean allFilesGranted() {')
end=s.find('\n    boolean usbHardwareGranted()',start)
s=s[:start]+'''    boolean allFilesGranted() { return true; }

'''+s[end:]
start=s.find('    void requestAllFilesAccess(){')
end=s.find('\n    void requestUsbHardwarePermission(){',start)
s=s[:start]+'''    void requestAllFilesAccess(){
        toast("O acesso aos arquivos é feito pelo seletor seguro do Android.");
        showSetupWizard();
    }

'''+s[end:]

# prefs / URIs
s=s.replace('''    boolean usbTreeGranted() {
        String u = prefs.getString("usb", null);
        return u != null && hasPersistedPermission(Uri.parse(u));
    }''','''    boolean usbTreeGranted() { return safeTreeUri("usb",true)!=null; }''',1)

s=s.replace('''    void restoreRoots() {
        String p = prefs.getString("phone", null), u = prefs.getString("usb", null);
        if (p != null && hasPersistedPermission(Uri.parse(p))) phone.setRoot(Uri.parse(p));
        if (u != null && hasPersistedPermission(Uri.parse(u))) usb.setRoot(Uri.parse(u));
    }

    boolean hasPersistedPermission(Uri uri) {
        for (UriPermission p : getContentResolver().getPersistedUriPermissions()) {
            if (p.getUri().equals(uri) && p.isReadPermission()) return true;
        }
        return false;
    }''','''    void restoreRoots() {
        if(phone==null||usb==null)return;
        Uri p=safeTreeUri("phone",false), u=safeTreeUri("usb",true);
        if(p!=null) phone.setRoot(p);
        if(u!=null) usb.setRoot(u);
    }

    boolean hasPersistedPermission(Uri uri){ return hasPersistedPermission(uri,false); }
    boolean hasPersistedPermission(Uri uri,boolean requireWrite) {
        if(uri==null)return false;
        try{
            for (UriPermission p : getContentResolver().getPersistedUriPermissions()) {
                if (p.getUri().equals(uri) && p.isReadPermission() && (!requireWrite || p.isWritePermission())) return true;
            }
        }catch(Throwable e){ BiggerApp.logNonFatal(this,"PERMISSION","Falha ao consultar URI persistida",e); }
        return false;
    }''',1)

# Android 5/6: não chamar API 24
s=s.replace('''    StorageVolume findRemovableVolume() {
        StorageManager sm = (StorageManager)getSystemService(STORAGE_SERVICE);
        if (sm == null) return null;
        try {
            for (StorageVolume v : sm.getStorageVolumes()) {
                if (v.isRemovable() && !v.isPrimary()) return v;
            }
        } catch (Exception ignored) {}
        return null;
    }''','''    StorageVolume findRemovableVolume() {
        if(Build.VERSION.SDK_INT<24)return null;
        StorageManager sm = (StorageManager)getSystemService(STORAGE_SERVICE);
        if (sm == null) return null;
        try {
            for (StorageVolume v : sm.getStorageVolumes()) {
                if (v.isRemovable() && !v.isPrimary()) return v;
            }
        } catch (Throwable e) { BiggerApp.logNonFatal(this,"USB_OTG","Falha ao listar volumes",e); }
        return null;
    }''',1)

# USB salvo seguro
s=s.replace('''        String saved = prefs.getString("usb", null);
        if (saved != null) {
            Uri u = Uri.parse(saved);
            if (hasPersistedPermission(u) && (uuid == null || saved.toLowerCase(Locale.ROOT).contains(uuid.toLowerCase(Locale.ROOT)))) return u;
        }''','''        String saved = safePrefString("usb");
        if (saved != null) {
            try{
                Uri u = Uri.parse(saved);
                if (hasPersistedPermission(u,true) && (uuid == null || saved.toLowerCase(Locale.ROOT).contains(uuid.toLowerCase(Locale.ROOT)))) return u;
            }catch(Throwable e){
                BiggerApp.logNonFatal(this,"USB_OTG","URI USB salva inválida",e);
                prefs.edit().remove("usb").apply();
            }
        }''',1)

# Pane virtualizada
s=s.replace('''        final boolean isUsb; final LinearLayout view, list; final TextView path, count; final EditText search;
        Uri treeUri; String rootDocId, currentDocId; final ArrayDeque<String> stack = new ArrayDeque<>();
        final LinkedHashMap<String,Node> selected = new LinkedHashMap<>(); List<Node> currentNodes = new ArrayList<>();''','''        final boolean isUsb; final LinearLayout view; final ListView list; final TextView path, count; final EditText search;
        Uri treeUri; String rootDocId, currentDocId; final ArrayDeque<String> stack = new ArrayDeque<>();
        final LinkedHashMap<String,Node> selected = new LinkedHashMap<>();
        List<Node> currentNodes = new ArrayList<>();
        final ArrayList<Node> visibleNodes = new ArrayList<>();
        final BaseAdapter fileAdapter;
        int loadGeneration=0;''',1)

old='''            count=txt("0 itens",12,SOFT,false); count.setPadding(dp(4),dp(6),0,dp(4)); view.addView(count);
            list=new LinearLayout(MainActivity.this); list.setOrientation(LinearLayout.VERTICAL); view.addView(list);
        }

        void showDisconnected(){ if(isUsb){ treeUri=null; rootDocId=null; currentDocId=null; stack.clear(); selected.clear(); currentNodes.clear(); path.setText("Pendrive desconectado"); render(); } }
        void setRoot(Uri uri){ treeUri=uri; rootDocId=DocumentsContract.getTreeDocumentId(uri); currentDocId=rootDocId; stack.clear(); selected.clear(); load(); }'''
new='''            count=txt("0 itens",12,SOFT,false); count.setPadding(dp(4),dp(6),0,dp(4)); view.addView(count);
            list=new ListView(MainActivity.this); list.setDividerHeight(dp(4)); list.setClipToPadding(false);
            fileAdapter=new BaseAdapter(){
                public int getCount(){return visibleNodes.size();}
                public Object getItem(int p){return visibleNodes.get(p);}
                public long getItemId(int p){return p;}
                public View getView(int p,View convert,ViewGroup parent){return row(visibleNodes.get(p));}
            };
            list.setAdapter(fileAdapter);
            int h=Math.max(dp(190),Math.min(dp(340),getResources().getDisplayMetrics().heightPixels/3));
            view.addView(list,new LinearLayout.LayoutParams(-1,h));
        }

        void showDisconnected(){ if(isUsb){ loadGeneration++; treeUri=null; rootDocId=null; currentDocId=null; stack.clear(); selected.clear(); currentNodes.clear(); path.setText("Dispositivo USB removido ou indisponível."); render(); } }
        void setRoot(Uri uri){
            try{
                if(uri==null||!"content".equalsIgnoreCase(uri.getScheme())||!DocumentsContract.isTreeUri(uri))throw new IllegalArgumentException("Árvore inválida");
                treeUri=uri; rootDocId=DocumentsContract.getTreeDocumentId(uri); currentDocId=rootDocId; stack.clear(); selected.clear(); load();
            }catch(Throwable e){
                BiggerApp.logNonFatal(MainActivity.this,isUsb?"USB_OTG":"STORAGE","Falha ao abrir raiz SAF",e);
                if(isUsb)prefs.edit().remove("usb").apply(); else prefs.edit().remove("phone").apply();
                treeUri=null;rootDocId=null;currentDocId=null;currentNodes.clear();selected.clear();
                path.setText(isUsb?"USB indisponível. Autorize novamente.":"Pasta indisponível. Abra novamente.");
                render();
            }
        }'''
if old not in s: raise SystemExit("Pane init não encontrado")
s=s.replace(old,new,1)

# load/render seguros e sem milhares de Views
old='''        void load(){
            if(treeUri==null)return;
            path.setText("Carregando...");
            io.execute(()->{
                List<Node> nodes=queryChildren(treeUri,currentDocId);
                runOnUiThread(()->{ currentNodes=nodes; path.setText((isUsb?"USB: ":"Celular: ")+friendlyPath()); render(); });
            });
        }
        String friendlyPath(){ return stack.isEmpty()?"Raiz selecionada":"Pasta atual"; }
        void render(){
            list.removeAllViews(); String q=search.getText().toString().trim().toLowerCase(Locale.ROOT); int shown=0;
            for(Node n:currentNodes){ if(!q.isEmpty() && !n.name.toLowerCase(Locale.ROOT).contains(q))continue; shown++; list.addView(row(n)); }
            count.setText(shown+" itens • "+selected.size()+" selecionados");
            if(shown==0){ TextView empty=txt(treeUri==null?(isUsb?"Conecte o OTG":"Abra uma pasta"):"Pasta vazia",14,SOFT,false); empty.setGravity(Gravity.CENTER); empty.setPadding(0,dp(20),0,dp(20)); list.addView(empty); }
        }'''
new='''        void load(){
            if(treeUri==null)return;
            final Uri tree=treeUri; final String doc=currentDocId; final int gen=++loadGeneration;
            path.setText("Carregando...");
            io.execute(()->{
                try{
                    List<Node> nodes=queryChildrenStrict(tree,doc);
                    safeUi(()->{
                        if(gen!=loadGeneration||!Objects.equals(treeUri,tree)||!Objects.equals(currentDocId,doc))return;
                        currentNodes=nodes; path.setText((isUsb?"USB: ":"Celular: ")+friendlyPath()); render();
                    });
                }catch(Throwable e){
                    BiggerApp.logNonFatal(MainActivity.this,isUsb?"USB_OTG":"FILE_MANAGER","Falha ao listar pasta",e);
                    safeUi(()->{
                        if(gen!=loadGeneration)return;
                        currentNodes.clear();selected.clear();
                        path.setText(isUsb?"Dispositivo USB removido ou indisponível.":"Pasta indisponível ou permissão revogada.");
                        render();
                    });
                }
            });
        }
        String friendlyPath(){ return stack.isEmpty()?"Raiz selecionada":"Pasta atual"; }
        void render(){
            visibleNodes.clear();
            String q=search.getText().toString().trim().toLowerCase(Locale.ROOT);
            for(Node n:currentNodes){
                String nn=n.name==null?"":n.name;
                if(q.isEmpty()||nn.toLowerCase(Locale.ROOT).contains(q))visibleNodes.add(n);
            }
            fileAdapter.notifyDataSetChanged();
            count.setText(visibleNodes.size()+" itens • "+selected.size()+" selecionados");
            list.setEmptyView(null);
        }'''
if old not in s: raise SystemExit("load/render não encontrado")
s=s.replace(old,new,1)

# query estrita
old='''    List<Node> queryChildren(Uri tree,String parentId){
        ArrayList<Node> out=new ArrayList<>(); if(tree==null||parentId==null)return out; Uri children=DocumentsContract.buildChildDocumentsUriUsingTree(tree,parentId);
        String[] p={DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_MIME_TYPE,DocumentsContract.Document.COLUMN_SIZE,DocumentsContract.Document.COLUMN_LAST_MODIFIED};
        try(Cursor c=getContentResolver().query(children,p,null,null,null)){
            if(c!=null)while(c.moveToNext()){ Node n=new Node(); n.id=c.getString(0); n.name=c.getString(1)==null?"Sem nome":c.getString(1); n.mime=c.getString(2); n.dir=DocumentsContract.Document.MIME_TYPE_DIR.equals(n.mime); n.size=c.isNull(3)?0:c.getLong(3); n.modified=c.isNull(4)?0:c.getLong(4); out.add(n); }
        }catch(Exception ignored){}
        Collections.sort(out,(a,b)->{ if(a.dir!=b.dir)return a.dir?-1:1; return a.name.compareToIgnoreCase(b.name); }); return out;
    }'''
new='''    List<Node> queryChildrenStrict(Uri tree,String parentId)throws Exception{
        ArrayList<Node> out=new ArrayList<>(); if(tree==null||parentId==null)return out;
        Uri children=DocumentsContract.buildChildDocumentsUriUsingTree(tree,parentId);
        String[] p={DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_MIME_TYPE,DocumentsContract.Document.COLUMN_SIZE,DocumentsContract.Document.COLUMN_LAST_MODIFIED};
        try(Cursor c=getContentResolver().query(children,p,null,null,null)){
            if(c==null)throw new java.io.IOException("Provider não retornou cursor");
            while(c.moveToNext()){
                Node n=new Node(); n.id=c.getString(0); n.name=c.getString(1)==null?"Sem nome":c.getString(1); n.mime=c.getString(2);
                n.dir=DocumentsContract.Document.MIME_TYPE_DIR.equals(n.mime); n.size=c.isNull(3)?0:c.getLong(3); n.modified=c.isNull(4)?0:c.getLong(4); out.add(n);
            }
        }
        Collections.sort(out,(a,b)->{ if(a.dir!=b.dir)return a.dir?-1:1; return String.valueOf(a.name).compareToIgnoreCase(String.valueOf(b.name)); });
        return out;
    }
    List<Node> queryChildren(Uri tree,String parentId){
        try{return queryChildrenStrict(tree,parentId);}
        catch(Throwable e){BiggerApp.logNonFatal(this,"FILE_MANAGER","queryChildren",e);return new ArrayList<>();}
    }'''
if old not in s: raise SystemExit("queryChildren não encontrado")
s=s.replace(old,new,1)

# transferência: trava clique duplo + lifecycle
start=s.find('    void transfer(Pane src, Pane dst, boolean move){')
end=s.find('\n    boolean copyNode(Uri srcTree, Node source, Uri dstTree, String dstParentId){',start)
if start<0 or end<0: raise SystemExit("transfer não encontrado")
newtransfer=r'''    void transfer(Pane src, Pane dst, boolean move){
        if(transferBusy){toast("Já existe uma transferência em andamento.");return;}
        if(dst==null||src==null||dst.treeUri==null||dst.currentDocId==null||(src.treeUri==null&&!hasExternalSelection(src))){toast("Abra o celular e o USB primeiro.");return;}
        if(src.selected.isEmpty()){toast("Selecione pelo menos um arquivo.");return;}
        transferBusy=true;
        BiggerApp.markAction(this,move?"MOVE_FILES":"COPY_FILES");
        ArrayList<Node> jobs=new ArrayList<>(src.selected.values());
        ProgressDialog pd=new ProgressDialog(this); pd.setTitle(move?"Movendo arquivos":"Copiando arquivos"); pd.setProgressStyle(ProgressDialog.STYLE_HORIZONTAL); pd.setMax(jobs.size()); pd.setCancelable(false);
        try{pd.show();}catch(Throwable e){BiggerApp.logNonFatal(this,"FILE_MANAGER","Mostrar progresso",e);}
        io.execute(()->{
            int ok=0; String lastError=null;
            try{
                for(int i=0;i<jobs.size();i++){
                    Node n=jobs.get(i); final int pos=i;
                    safeUi(()->{if(pd.isShowing()){pd.setMessage(n.name);pd.setProgress(pos);}});
                    boolean copied=copyNode(src.treeUri,n,dst.treeUri,dst.currentDocId,0);
                    if(copied){
                        ok++;
                        if(move)deleteSourceNode(src,n);
                    }else lastError="Falha ao copiar "+n.name;
                }
            }catch(Throwable e){
                lastError=e.getMessage();
                BiggerApp.logNonFatal(this,"FILE_MANAGER","Transferência",e);
            }
            final int total=jobs.size(),good=ok; final String err=lastError;
            safeUi(()->{
                transferBusy=false;
                try{if(pd.isShowing())pd.dismiss();}catch(Throwable ignored){}
                src.selected.clear();
                toast(good+" de "+total+(move?" movido(s).":" copiado(s).")+(err!=null&&good<total?" • Verifique o dispositivo.":""));
                src.load();dst.load();
            });
        });
    }

    void deleteSourceNode(Pane src,Node n){
        try{
            if(n.externalUri!=null&&"file".equalsIgnoreCase(n.externalUri.getScheme())){
                java.io.File f=new java.io.File(n.externalUri.getPath());
                if(f.exists()&&!f.delete())throw new java.io.IOException("Não foi possível remover origem");
            }else if(n.externalUri!=null){
                DocumentsContract.deleteDocument(getContentResolver(),n.externalUri);
            }else{
                DocumentsContract.deleteDocument(getContentResolver(),docUri(src.treeUri,n.id));
            }
        }catch(Throwable e){BiggerApp.logNonFatal(this,"FILE_MANAGER","Falha ao remover origem",e);}
    }

'''
s=s[:start]+newtransfer+s[end:]

# copy recursiva protegida + file://
start=s.find('    boolean copyNode(Uri srcTree, Node source, Uri dstTree, String dstParentId){')
end=s.find('\n    String uniqueName(',start)
oldblock=s[start:end]
newcopy=r'''    boolean copyNode(Uri srcTree, Node source, Uri dstTree, String dstParentId){return copyNode(srcTree,source,dstTree,dstParentId,0);}
    boolean copyNode(Uri srcTree, Node source, Uri dstTree, String dstParentId,int depth){
        if(depth>64)return false;
        Uri made=null;
        try{
            Uri dstParent=docUri(dstTree,dstParentId); String name=uniqueName(dstTree,dstParentId,safeFileName(source.name));
            if(source.dir){
                made=DocumentsContract.createDocument(getContentResolver(),dstParent,DocumentsContract.Document.MIME_TYPE_DIR,name);
                if(made==null)return false;
                String newId=DocumentsContract.getDocumentId(made);
                for(Node child:queryChildrenStrict(srcTree,source.id)) if(!copyNode(srcTree,child,dstTree,newId,depth+1))return false;
                return true;
            }
            String mime=(source.mime==null||source.mime.isEmpty())?"application/octet-stream":source.mime;
            made=DocumentsContract.createDocument(getContentResolver(),dstParent,mime,name); if(made==null)return false;
            InputStream rawIn;
            if(source.externalUri!=null&&"file".equalsIgnoreCase(source.externalUri.getScheme())) rawIn=new java.io.FileInputStream(new java.io.File(source.externalUri.getPath()));
            else{
                Uri sourceUri=source.externalUri!=null?source.externalUri:docUri(srcTree,source.id);
                rawIn=getContentResolver().openInputStream(sourceUri);
            }
            try(InputStream in=new java.io.BufferedInputStream(rawIn);OutputStream rawOut=getContentResolver().openOutputStream(made,"w")){
                if(in==null||rawOut==null)throw new java.io.IOException("Fluxo indisponível");
                try(OutputStream out=new java.io.BufferedOutputStream(rawOut)){
                    byte[] buf=new byte[128*1024];int r;while((r=in.read(buf))>0)out.write(buf,0,r);out.flush();
                }
            }
            return true;
        }catch(Throwable e){
            BiggerApp.logNonFatal(this,"FILE_MANAGER","copyNode: "+(source==null?"?":source.name),e);
            if(made!=null)try{DocumentsContract.deleteDocument(getContentResolver(),made);}catch(Throwable ignored){}
            return false;
        }
    }

    String safeFileName(String original){
        String n=original==null?"arquivo":original.replaceAll("[\\\\/:*?\"<>|]","_").trim();
        if(n.isEmpty())n="arquivo";
        if(n.length()>180){
            String ext="";int dot=n.lastIndexOf('.');
            if(dot>0&&n.length()-dot<=12){ext=n.substring(dot);n=n.substring(0,Math.min(dot,180-ext.length()))+ext;}
            else n=n.substring(0,180);
        }
        return n;
    }

'''
s=s[:start]+newcopy+s[end:]

# APK/thumbnail: nada pesado na UI + cache limitado
s=s.replace('''        // APK local extraído pelo próprio app: caminho direto.
        if(isApkNode(n)){
            android.graphics.drawable.Drawable direct=extractedApkIcon(n);
            if(direct!=null){
                fileVisualCache.put(key,direct);
                setCompoundApkIcon(tv,direct,n.name);
                return;
            }
        }

        if(sourceUri==null||fileVisualLoading.contains(key))return;''','''        if(sourceUri==null||fileVisualLoading.contains(key))return;''',1)
s=s.replace('try { fileVisualCache.put(key,result); } catch (Throwable ignored) {}','try { putVisualCache(key,result); } catch (Throwable e) { BiggerApp.logNonFatal(this,"APK_ICON","cache",e); }',1)

# imagem com amostragem, sem decode integral
old='''                try(InputStream in=getContentResolver().openInputStream(sourceUri)){
                    if(in!=null){
                        android.graphics.BitmapFactory.Options o=new android.graphics.BitmapFactory.Options();
                        o.inJustDecodeBounds=true;android.graphics.BitmapFactory.decodeStream(in,null,o);
                    }
                } catch(Exception ignored){}
                try(InputStream in2=getContentResolver().openInputStream(sourceUri)){
                    if(in2!=null){
                        android.graphics.Bitmap b=android.graphics.BitmapFactory.decodeStream(in2);
                        if(b!=null)return new android.graphics.drawable.BitmapDrawable(getResources(),b);
                    }
                }'''
new='''                try{
                    android.graphics.Bitmap b=decodeSampledBitmap(sourceUri,192,192);
                    if(b!=null)return new android.graphics.drawable.BitmapDrawable(getResources(),b);
                }catch(Throwable e){BiggerApp.logNonFatal(this,"FILE_MANAGER","Thumbnail de imagem",e);}'''
if old in s:s=s.replace(old,new,1)

# helper bitmap
marker='    android.graphics.drawable.Drawable loadVisualFromUri(Node n,Uri sourceUri) {'
bitmap=r'''    android.graphics.Bitmap decodeSampledBitmap(Uri uri,int reqW,int reqH)throws Exception{
        android.graphics.BitmapFactory.Options bounds=new android.graphics.BitmapFactory.Options();bounds.inJustDecodeBounds=true;
        try(InputStream in=getContentResolver().openInputStream(uri)){if(in==null)return null;android.graphics.BitmapFactory.decodeStream(in,null,bounds);}
        int sample=1;
        while(bounds.outWidth/sample>reqW*2||bounds.outHeight/sample>reqH*2)sample*=2;
        android.graphics.BitmapFactory.Options opts=new android.graphics.BitmapFactory.Options();opts.inSampleSize=Math.max(1,sample);opts.inPreferredConfig=android.graphics.Bitmap.Config.RGB_565;
        try(InputStream in=getContentResolver().openInputStream(uri)){if(in==null)return null;return android.graphics.BitmapFactory.decodeStream(in,null,opts);}
    }

'''
s=s.replace(marker,bitmap+marker,1)

# logged catches vazios principais
s=s.replace('catch (Exception e) { return null; }','catch (Exception e) { BiggerApp.logNonFatal(this,"SHARE_INTENT","getSharedUri",e); return null; }',1)

m.write_text(s)

# Manifest/Gradle
man=Path("buildsrc/app/src/main/AndroidManifest.xml")
ms=man.read_text()
for perm in [
'    <uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE" />\n',
'    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />\n',
'    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="29" />\n']:
    ms=ms.replace(perm,'')
ms=ms.replace('<application android:allowBackup="true"','<application android:name=".BiggerApp" android:allowBackup="false"',1)
man.write_text(ms)

Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/BiggerApp.java").write_text(Path("v7/BiggerApp.java").read_text())

b=Path("buildsrc/app/build.gradle")
g=b.read_text().replace('versionCode 14','versionCode 15').replace("versionName '6.6.0'","versionName '7.0.0'")
b.write_text(g)
