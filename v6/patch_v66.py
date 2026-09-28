from pathlib import Path

p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java")
s=p.read_text()

# 1) Captura de paths extraídos: consumir e limpar ANTES de processar.
start=s.find('    void captureExtractedPaths(Intent intent) {')
end=s.find('\n    void captureSharedIntent(Intent intent) {',start)
if start<0 or end<0:
    raise SystemExit("captureExtractedPaths não encontrado")

new=r'''    void captureExtractedPaths(Intent intent) {
        if (intent == null) return;
        ArrayList<String> paths = null;
        try {
            paths = intent.getStringArrayListExtra("bigger_extracted_paths");
            intent.removeExtra("bigger_extracted_paths");
            setIntent(new Intent(this, MainActivity.class));
        } catch (Throwable ignored) {}

        if (paths == null || paths.isEmpty()) return;

        ArrayList<Uri> safeUris = new ArrayList<>();
        for (String path : paths) {
            try {
                if (path == null || path.trim().isEmpty()) continue;
                java.io.File f = new java.io.File(path);
                if (!f.exists() || !f.isFile() || f.length() <= 0) continue;
                safeUris.add(Uri.fromFile(f));
            } catch (Throwable ignored) {}
        }

        if (!safeUris.isEmpty()) {
            pendingSharedUris.addAll(safeUris);
        }
    }

'''
s=s[:start]+new+s[end:]

# 2) Não zerar/alterar intent duas vezes depois da captura.
s=s.replace('''captureSharedIntent(getIntent());
        captureExtractedPaths(getIntent());
        try { setIntent(new Intent(this, MainActivity.class)); } catch (Throwable ignored) {}''',
'''Intent launchIntent = getIntent();
        captureExtractedPaths(launchIntent);
        captureSharedIntent(launchIntent);''',1)

s=s.replace('''captureSharedIntent(intent);
        captureExtractedPaths(intent);
        try { setIntent(new Intent(this, MainActivity.class)); } catch (Throwable ignored) {}''',
'''captureExtractedPaths(intent);
        captureSharedIntent(intent);''',1)

# 3) extractedApkIcon: proteção total contra APK quebrado/recurso inválido
start=s.find('    android.graphics.drawable.Drawable extractedApkIcon(Node n) {')
end=s.find('\n    View fileVisual(Node n) {',start)
if start<0 or end<0:
    raise SystemExit("extractedApkIcon não encontrado")

safe_icon=r'''    android.graphics.drawable.Drawable extractedApkIcon(Node n) {
        if (n == null || n.dir || n.name == null || !n.name.toLowerCase(Locale.ROOT).endsWith(".apk")) return null;
        try {
            String path = null;
            if (n.externalUri != null && "file".equalsIgnoreCase(n.externalUri.getScheme())) path = n.externalUri.getPath();
            if (path == null || path.isEmpty()) return null;

            java.io.File f = new java.io.File(path);
            if (!f.exists() || !f.isFile() || f.length() <= 0) return null;

            android.content.pm.PackageManager pm = getPackageManager();
            android.content.pm.PackageInfo pi;
            if (Build.VERSION.SDK_INT >= 33) {
                pi = pm.getPackageArchiveInfo(path, android.content.pm.PackageManager.PackageInfoFlags.of(0));
            } else {
                pi = pm.getPackageArchiveInfo(path, 0);
            }
            if (pi == null || pi.applicationInfo == null) return null;

            pi.applicationInfo.sourceDir = path;
            pi.applicationInfo.publicSourceDir = path;
            try {
                return pi.applicationInfo.loadIcon(pm);
            } catch (Throwable ignored) {
                return null;
            }
        } catch (Throwable ignored) {
            return null;
        }
    }

'''
s=s[:start]+safe_icon+s[end:]

# 4) applyPendingSharedFiles: sempre limpar pendências, mesmo se alguma falhar.
old='''        if (incoming.isEmpty()) return;
        phone.showIncoming(incoming);
        pendingSharedUris.clear();
        toast(incoming.size() == 1 ? "Arquivo recebido e selecionado." : incoming.size()+" arquivos recebidos e selecionados.");'''
new='''        pendingSharedUris.clear();
        if (incoming.isEmpty()) return;
        try {
            phone.showIncoming(incoming);
            toast(incoming.size() == 1 ? "Arquivo recebido e selecionado." : incoming.size()+" arquivos recebidos e selecionados.");
        } catch (Throwable ignored) {
            toast("Arquivo recebido. Abra a pasta do celular para localizar.");
        }'''
if old not in s:
    raise SystemExit("applyPendingSharedFiles final não encontrado")
s=s.replace(old,new,1)

# 5) Loader visual: qualquer erro jamais derruba a UI
old='''        io.execute(()->{
            android.graphics.drawable.Drawable found=loadVisualFromUri(n,sourceUri);
            if(found==null)found=fallbackDrawableFor(n);
            fileVisualCache.put(key,found);
            fileVisualLoading.remove(key);
            android.graphics.drawable.Drawable result=found;
            runOnUiThread(()->{
                Object tag=tv.getTag();
                if(tag!=null&&key.equals(tag.toString()))setCompoundApkIcon(tv,result,n.name);
            });
        });'''
# Pode já ter sido alterado pela v6.4; substitui bloco atual também.
current='''        io.execute(()->{
            android.graphics.drawable.Drawable found=loadVisualFromUri(n,sourceUri);
            fileVisualLoading.remove(key);
            android.graphics.drawable.Drawable result=found;
            if(result!=null) fileVisualCache.put(key,result);
            runOnUiThread(()->{
                Object tag=tv.getTag();
                if(tag!=null&&key.equals(tag.toString())){
                    if(result!=null) setCompoundApkIcon(tv,result,n.name);
                    else tv.setText(icon(n)+"  "+n.name);
                }
            });
        });'''
safer='''        io.execute(()->{
            android.graphics.drawable.Drawable found=null;
            try { found=loadVisualFromUri(n,sourceUri); } catch (Throwable ignored) {}
            try { fileVisualLoading.remove(key); } catch (Throwable ignored) {}
            android.graphics.drawable.Drawable result=found;
            if(result!=null) {
                try { fileVisualCache.put(key,result); } catch (Throwable ignored) {}
            }
            runOnUiThread(()->{
                try {
                    Object tag=tv.getTag();
                    if(tag!=null&&key.equals(tag.toString())){
                        if(result!=null) setCompoundApkIcon(tv,result,n.name);
                        else {
                            tv.setCompoundDrawables(null,null,null,null);
                            tv.setText(icon(n)+"  "+n.name);
                        }
                    }
                } catch (Throwable ignored) {}
            });
        });'''
if current in s:
    s=s.replace(current,safer,1)
elif old in s:
    s=s.replace(old,safer,1)
else:
    raise SystemExit("loader assíncrono não encontrado")

p.write_text(s)

# AppsActivity: não fecha a tela antes de confirmar que o MainActivity recebeu;
# usa cache privado para extração normal, evitando scoped-storage e paths frágeis.
a=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/AppsActivity.java")
x=a.read_text()

oldroot='''File root=new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),"BIGGER OTG/APKs Extraidos");if(!root.exists())root.mkdirs();'''
newroot='''File root=new File(getCacheDir(),"extracted_apks");if(!root.exists())root.mkdirs();'''
if oldroot not in x:
    raise SystemExit("pasta raiz de extração não encontrada")
x=x.replace(oldroot,newroot,1)

# openInBigger mais seguro
start=x.find('    void openInBigger(ArrayList<String> paths){')
end=x.find('\n    void copy(File a,File b)',start)
if start<0 or end<0:
    raise SystemExit("openInBigger não encontrado")
newopen=r'''    void openInBigger(ArrayList<String> paths){
        if(paths==null||paths.isEmpty()){
            toast("Não foi possível preparar o APK extraído.");
            return;
        }
        ArrayList<String> valid=new ArrayList<>();
        for(String path:paths){
            try{
                File f=new File(path);
                if(f.exists()&&f.isFile()&&f.length()>0)valid.add(f.getAbsolutePath());
            }catch(Throwable ignored){}
        }
        if(valid.isEmpty()){
            toast("O APK extraído ficou vazio ou inválido.");
            return;
        }
        try{
            Intent i=new Intent(this,MainActivity.class);
            i.putStringArrayListExtra("bigger_extracted_paths",valid);
            i.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(i);
            finish();
        }catch(Throwable e){
            toast("APK extraído. Volte à tela principal.");
        }
    }

'''
x=x[:start]+newopen+x[end:]
a.write_text(x)

# versão
b=Path("buildsrc/app/build.gradle")
g=b.read_text().replace('versionCode 13','versionCode 14').replace("versionName '6.5.0'","versionName '6.6.0'")
b.write_text(g)
