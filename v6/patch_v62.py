from pathlib import Path

p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java")
s=p.read_text()

# Cache de ícones APK carregados de SAF/USB
needle='    int safeBaseLeft = 0, safeBaseTop = 0, safeBaseRight = 0, safeBaseBottom = 0;\n'
insert='''    int safeBaseLeft = 0, safeBaseTop = 0, safeBaseRight = 0, safeBaseBottom = 0;
    final java.util.concurrent.ConcurrentHashMap<String, android.graphics.drawable.Drawable> apkIconCache = new java.util.concurrent.ConcurrentHashMap<>();
    final java.util.Set<String> apkIconLoading = java.util.Collections.synchronizedSet(new java.util.HashSet<>());
'''
if needle not in s:
    raise SystemExit("Campos v6 não encontrados")
s=s.replace(needle,insert,1)

# Adiciona loader assíncrono antes de registerUsbReceiver
marker='    void registerUsbReceiver() {'
methods=r'''    boolean isApkNode(Node n) {
        if (n == null || n.dir || n.name == null) return false;
        String name=n.name.toLowerCase(Locale.ROOT);
        String mime=n.mime==null?"":n.mime.toLowerCase(Locale.ROOT);
        return name.endsWith(".apk") || mime.contains("android.package");
    }

    String apkIconKey(Node n, Uri source) {
        if (source != null) return source.toString();
        if (n != null && n.id != null) return n.id;
        return n == null ? "apk" : String.valueOf(n.name);
    }

    void setCompoundApkIcon(TextView tv, android.graphics.drawable.Drawable d, String text) {
        if (tv == null) return;
        tv.setText(text);
        if (d == null) {
            tv.setCompoundDrawables(null,null,null,null);
            return;
        }
        android.graphics.drawable.Drawable copy=d.getConstantState()!=null?d.getConstantState().newDrawable().mutate():d;
        copy.setBounds(0,0,dp(30),dp(30));
        tv.setCompoundDrawables(copy,null,null,null);
        tv.setCompoundDrawablePadding(dp(9));
    }

    void applySmartFileIcon(TextView tv, Node n, Uri sourceUri) {
        if (tv == null || n == null) return;
        tv.setCompoundDrawables(null,null,null,null);

        if (n.dir) {
            tv.setText("📁  "+n.name);
            return;
        }

        if (!isApkNode(n)) {
            tv.setText(icon(n)+"  "+n.name);
            return;
        }

        String key=apkIconKey(n,sourceUri);
        tv.setTag(key);
        android.graphics.drawable.Drawable cached=apkIconCache.get(key);
        if (cached != null) {
            setCompoundApkIcon(tv,cached,n.name);
            return;
        }

        android.graphics.drawable.Drawable direct=extractedApkIcon(n);
        if (direct != null) {
            apkIconCache.put(key,direct);
            setCompoundApkIcon(tv,direct,n.name);
            return;
        }

        tv.setText("📦  "+n.name);
        if (sourceUri == null || apkIconLoading.contains(key)) return;
        apkIconLoading.add(key);

        io.execute(() -> {
            android.graphics.drawable.Drawable found=null;
            java.io.File tmp=null;
            try {
                tmp=new java.io.File(getCacheDir(),"bigger_icon_"+Math.abs(key.hashCode())+"_"+System.nanoTime()+".apk");
                try(InputStream in=getContentResolver().openInputStream(sourceUri);
                    OutputStream out=new java.io.FileOutputStream(tmp)) {
                    if(in==null) throw new java.io.IOException("Arquivo não disponível");
                    byte[] buf=new byte[262144];
                    int r;
                    while((r=in.read(buf))>0) out.write(buf,0,r);
                    out.flush();
                }

                android.content.pm.PackageManager pm=getPackageManager();
                android.content.pm.PackageInfo pi=pm.getPackageArchiveInfo(tmp.getAbsolutePath(),0);
                if(pi!=null && pi.applicationInfo!=null) {
                    pi.applicationInfo.sourceDir=tmp.getAbsolutePath();
                    pi.applicationInfo.publicSourceDir=tmp.getAbsolutePath();
                    found=pi.applicationInfo.loadIcon(pm);
                }
            } catch(Exception ignored) {
            } finally {
                if(tmp!=null) try{tmp.delete();}catch(Exception ignored){}
                apkIconLoading.remove(key);
            }

            android.graphics.drawable.Drawable result=found;
            if(result!=null) apkIconCache.put(key,result);
            runOnUiThread(() -> {
                Object tag=tv.getTag();
                if(tag!=null && key.equals(tag.toString())) {
                    if(result!=null) setCompoundApkIcon(tv,result,n.name);
                    else tv.setText("📦  "+n.name);
                }
            });
        });
    }

'''
if marker not in s:
    raise SystemExit("registerUsbReceiver não encontrado")
s=s.replace(marker,methods+marker,1)

# Troca o bloco visual criado na v6.1 por versão assíncrona, usando URI SAF quando necessário
old='''            TextView nm=txt((n.dir?"📁  ":icon(n)+"  ")+n.name,15,Color.WHITE,n.dir);
            android.graphics.drawable.Drawable realApkIcon=extractedApkIcon(n);
            if(realApkIcon!=null){
                realApkIcon.setBounds(0,0,dp(28),dp(28));
                nm.setCompoundDrawables(realApkIcon,null,null,null);
                nm.setCompoundDrawablePadding(dp(8));
                nm.setText(n.name);
            }
            mid.addView(nm);'''
new='''            TextView nm=txt("",15,Color.WHITE,n.dir);
            Uri smartSource = n.externalUri != null ? n.externalUri : (treeUri != null && n.id != null ? docUri(treeUri,n.id) : null);
            applySmartFileIcon(nm,n,smartSource);
            mid.addView(nm);'''
if old not in s:
    raise SystemExit("Bloco visual v6.1 não encontrado")
s=s.replace(old,new,1)

p.write_text(s)

# Incrementa versão
b=Path("buildsrc/app/build.gradle")
g=b.read_text().replace('versionCode 9','versionCode 10').replace("versionName '6.1.0'","versionName '6.2.0'")
b.write_text(g)
