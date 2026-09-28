from pathlib import Path

p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java")
s=p.read_text()

# Acrescenta cache de miniaturas visuais
needle='''    final java.util.Set<String> apkIconLoading = java.util.Collections.synchronizedSet(new java.util.HashSet<>());
'''
insert='''    final java.util.Set<String> apkIconLoading = java.util.Collections.synchronizedSet(new java.util.HashSet<>());
    final java.util.concurrent.ConcurrentHashMap<String, android.graphics.drawable.Drawable> fileVisualCache = new java.util.concurrent.ConcurrentHashMap<>();
    final java.util.Set<String> fileVisualLoading = java.util.Collections.synchronizedSet(new java.util.HashSet<>());
'''
if needle not in s:
    raise SystemExit("cache v6.2 não encontrado")
s=s.replace(needle,insert,1)

# Substitui applySmartFileIcon por versão universal
start=s.find('    void applySmartFileIcon(TextView tv, Node n, Uri sourceUri) {')
end=s.find('\n    void registerUsbReceiver() {',start)
if start<0 or end<0:
    raise SystemExit("applySmartFileIcon não encontrado")

new_methods=r'''    android.graphics.drawable.Drawable fallbackDrawableFor(Node n) {
        TextView temp=txt(icon(n),22,Color.WHITE,false);
        temp.measure(
            View.MeasureSpec.makeMeasureSpec(dp(40),View.MeasureSpec.EXACTLY),
            View.MeasureSpec.makeMeasureSpec(dp(40),View.MeasureSpec.EXACTLY)
        );
        temp.layout(0,0,dp(40),dp(40));
        android.graphics.Bitmap bmp=android.graphics.Bitmap.createBitmap(dp(40),dp(40),android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas canvas=new android.graphics.Canvas(bmp);
        temp.draw(canvas);
        return new android.graphics.drawable.BitmapDrawable(getResources(),bmp);
    }

    android.graphics.drawable.Drawable loadVisualFromUri(Node n,Uri sourceUri) {
        if(sourceUri==null||n==null)return null;
        String name=n.name==null?"":n.name.toLowerCase(Locale.ROOT);
        String mime=n.mime==null?"":n.mime.toLowerCase(Locale.ROOT);

        try {
            if(isApkNode(n)) {
                java.io.File tmp=new java.io.File(getCacheDir(),"bigger_apk_"+Math.abs(sourceUri.toString().hashCode())+"_"+System.nanoTime()+".apk");
                try(InputStream in=getContentResolver().openInputStream(sourceUri);OutputStream out=new java.io.FileOutputStream(tmp)){
                    if(in==null)return null;
                    byte[] buf=new byte[262144];int r;
                    while((r=in.read(buf))>0)out.write(buf,0,r);
                    out.flush();
                }
                android.content.pm.PackageManager pm=getPackageManager();
                android.content.pm.PackageInfo pi;
                if(Build.VERSION.SDK_INT>=33) {
                    pi=pm.getPackageArchiveInfo(tmp.getAbsolutePath(),android.content.pm.PackageManager.PackageInfoFlags.of(0));
                } else {
                    pi=pm.getPackageArchiveInfo(tmp.getAbsolutePath(),0);
                }
                android.graphics.drawable.Drawable d=null;
                if(pi!=null&&pi.applicationInfo!=null){
                    pi.applicationInfo.sourceDir=tmp.getAbsolutePath();
                    pi.applicationInfo.publicSourceDir=tmp.getAbsolutePath();
                    d=pi.applicationInfo.loadIcon(pm);
                }
                try{tmp.delete();}catch(Exception ignored){}
                return d;
            }

            if(mime.startsWith("image/")||name.matches(".*\\.(jpg|jpeg|png|gif|webp|bmp|heic)$")) {
                if(Build.VERSION.SDK_INT>=29) {
                    try {
                        android.graphics.Bitmap b=getContentResolver().loadThumbnail(sourceUri,new android.util.Size(dp(96),dp(96)),null);
                        if(b!=null)return new android.graphics.drawable.BitmapDrawable(getResources(),b);
                    } catch(Exception ignored){}
                }
                try(InputStream in=getContentResolver().openInputStream(sourceUri)){
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
                }
            }

            if(mime.startsWith("video/")||name.matches(".*\\.(mp4|mkv|avi|mov|wmv|webm|m4v|ts)$")) {
                if(Build.VERSION.SDK_INT>=29){
                    try{
                        android.graphics.Bitmap b=getContentResolver().loadThumbnail(sourceUri,new android.util.Size(dp(96),dp(96)),null);
                        if(b!=null)return new android.graphics.drawable.BitmapDrawable(getResources(),b);
                    }catch(Exception ignored){}
                }
                android.media.MediaMetadataRetriever mmr=new android.media.MediaMetadataRetriever();
                try{
                    mmr.setDataSource(this,sourceUri);
                    android.graphics.Bitmap b=mmr.getFrameAtTime(0);
                    if(b!=null)return new android.graphics.drawable.BitmapDrawable(getResources(),b);
                }finally{try{mmr.release();}catch(Exception ignored){}}
            }

            if(mime.startsWith("audio/")||name.matches(".*\\.(mp3|wav|flac|aac|ogg|m4a|wma)$")) {
                android.media.MediaMetadataRetriever mmr=new android.media.MediaMetadataRetriever();
                try{
                    mmr.setDataSource(this,sourceUri);
                    byte[] art=mmr.getEmbeddedPicture();
                    if(art!=null){
                        android.graphics.Bitmap b=android.graphics.BitmapFactory.decodeByteArray(art,0,art.length);
                        if(b!=null)return new android.graphics.drawable.BitmapDrawable(getResources(),b);
                    }
                }finally{try{mmr.release();}catch(Exception ignored){}}
            }
        } catch(Exception ignored){}

        return null;
    }

    void applySmartFileIcon(TextView tv, Node n, Uri sourceUri) {
        if(tv==null||n==null)return;
        tv.setCompoundDrawables(null,null,null,null);

        if(n.dir){
            tv.setText("📁  "+n.name);
            return;
        }

        String key=(sourceUri!=null?sourceUri.toString():(n.id!=null?n.id:String.valueOf(n.name)));
        tv.setTag(key);

        android.graphics.drawable.Drawable cached=fileVisualCache.get(key);
        if(cached==null)cached=apkIconCache.get(key);
        if(cached!=null){
            setCompoundApkIcon(tv,cached,n.name);
            return;
        }

        // Nunca mostrar o antigo robô/caixa genérica como visual final.
        tv.setText(icon(n)+"  "+n.name);

        // APK local extraído pelo próprio app: caminho direto.
        if(isApkNode(n)){
            android.graphics.drawable.Drawable direct=extractedApkIcon(n);
            if(direct!=null){
                fileVisualCache.put(key,direct);
                setCompoundApkIcon(tv,direct,n.name);
                return;
            }
        }

        if(sourceUri==null||fileVisualLoading.contains(key))return;
        fileVisualLoading.add(key);

        io.execute(()->{
            android.graphics.drawable.Drawable found=loadVisualFromUri(n,sourceUri);
            if(found==null)found=fallbackDrawableFor(n);
            fileVisualCache.put(key,found);
            fileVisualLoading.remove(key);
            android.graphics.drawable.Drawable result=found;
            runOnUiThread(()->{
                Object tag=tv.getTag();
                if(tag!=null&&key.equals(tag.toString()))setCompoundApkIcon(tv,result,n.name);
            });
        });
    }

'''
s=s[:start]+new_methods+s[end:]

# Melhora o método icon: sem caixa genérica para APK
old='''        if(x.endsWith(".apk")||m.contains("android.package"))return "📦";'''
new='''        if(x.endsWith(".apk")||m.contains("android.package"))return "⬢";'''
if old in s:
    s=s.replace(old,new,1)

p.write_text(s)

# Incrementa versão
b=Path("buildsrc/app/build.gradle")
g=b.read_text().replace('versionCode 10','versionCode 11').replace("versionName '6.2.0'","versionName '6.3.0'")
b.write_text(g)
