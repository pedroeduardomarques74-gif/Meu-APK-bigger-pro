from pathlib import Path
import re

# ---------- MAIN ACTIVITY: ícones por tipo + ícone real do APK ----------
p = Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java")
s = p.read_text()

marker = '    void registerUsbReceiver() {'
helpers = r'''    String fileTypeEmoji(Node n) {
        if (n == null) return "📄";
        if (n.dir) return "📁";
        String name = n.name == null ? "" : n.name.toLowerCase(Locale.ROOT);
        String mime = n.mime == null ? "" : n.mime.toLowerCase(Locale.ROOT);

        if (name.endsWith(".apk") || mime.contains("android.package")) return "📦";
        if (mime.startsWith("audio/") || name.matches(".*\\.(mp3|wav|flac|aac|ogg|m4a|wma)$")) return "🎵";
        if (mime.startsWith("video/") || name.matches(".*\\.(mp4|mkv|avi|mov|wmv|webm|m4v|ts)$")) return "🎬";
        if (mime.startsWith("image/") || name.matches(".*\\.(jpg|jpeg|png|gif|webp|bmp|heic|svg)$")) return "🖼️";
        if (name.endsWith(".pdf") || mime.contains("pdf")) return "📕";
        if (name.matches(".*\\.(zip|rar|7z|tar|gz|bz2|xz)$") || mime.contains("zip") || mime.contains("compressed")) return "🗜️";
        if (name.matches(".*\\.(doc|docx|odt)$")) return "📝";
        if (name.matches(".*\\.(xls|xlsx|ods|csv)$")) return "📊";
        if (name.matches(".*\\.(ppt|pptx|odp)$")) return "📽️";
        if (mime.startsWith("text/") || name.matches(".*\\.(txt|log|json|xml|html|htm|md)$")) return "📄";
        return "📄";
    }

    android.graphics.drawable.Drawable extractedApkIcon(Node n) {
        if (n == null || n.dir || n.name == null || !n.name.toLowerCase(Locale.ROOT).endsWith(".apk")) return null;
        try {
            String path = null;
            if (n.externalUri != null && "file".equalsIgnoreCase(n.externalUri.getScheme())) {
                path = n.externalUri.getPath();
            }
            if (path == null || path.isEmpty()) return null;
            java.io.File f = new java.io.File(path);
            if (!f.exists() || f.length() <= 0) return null;
            android.content.pm.PackageManager pm = getPackageManager();
            android.content.pm.PackageInfo pi = pm.getPackageArchiveInfo(path, 0);
            if (pi == null || pi.applicationInfo == null) return null;
            pi.applicationInfo.sourceDir = path;
            pi.applicationInfo.publicSourceDir = path;
            return pi.applicationInfo.loadIcon(pm);
        } catch (Exception ignored) {
            return null;
        }
    }

    View fileVisual(Node n) {
        android.graphics.drawable.Drawable apkIcon = extractedApkIcon(n);
        if (apkIcon != null) {
            ImageView iv = new ImageView(this);
            iv.setImageDrawable(apkIcon);
            iv.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
            iv.setPadding(dp(2), dp(2), dp(2), dp(2));
            return iv;
        }
        TextView tv = txt(fileTypeEmoji(n), 19, Color.WHITE, false);
        tv.setGravity(Gravity.CENTER);
        return tv;
    }

'''
if marker not in s:
    raise SystemExit("marker MainActivity não encontrado")
s = s.replace(marker, helpers + marker, 1)

# Troca o ícone genérico da linha por visual inteligente.
old_row = '''            TextView nm=txt((n.dir?"📁  ":icon(n)+"  ")+n.name,15,Color.WHITE,n.dir); mid.addView(nm);'''
new_row = '''            TextView nm=txt((n.dir?"📁  ":icon(n)+"  ")+n.name,15,Color.WHITE,n.dir);
            android.graphics.drawable.Drawable realApkIcon=extractedApkIcon(n);
            if(realApkIcon!=null){
                realApkIcon.setBounds(0,0,dp(28),dp(28));
                nm.setCompoundDrawables(realApkIcon,null,null,null);
                nm.setCompoundDrawablePadding(dp(8));
                nm.setText(n.name);
            }
            mid.addView(nm);'''
if old_row not in s:
    raise SystemExit("Linha visual da lista de arquivos não encontrada")
s=s.replace(old_row,new_row,1)

old_icon = '''    String icon(Node n){ String x=n.name.toLowerCase(Locale.ROOT); if(n.mime!=null&&n.mime.startsWith("image/"))return "🖼"; if(n.mime!=null&&n.mime.startsWith("video/"))return "🎬"; if(n.mime!=null&&n.mime.startsWith("audio/"))return "🎵"; if(x.endsWith(".apk"))return "🤖"; if(x.endsWith(".zip")||x.endsWith(".rar")||x.endsWith(".7z"))return "🗜"; return "📄"; }'''
new_icon = r'''    String icon(Node n){
        String x=n.name==null?"":n.name.toLowerCase(Locale.ROOT);
        String m=n.mime==null?"":n.mime.toLowerCase(Locale.ROOT);
        if(m.startsWith("image/")||x.matches(".*\\.(jpg|jpeg|png|gif|webp|bmp|heic|svg)$"))return "🖼️";
        if(m.startsWith("video/")||x.matches(".*\\.(mp4|mkv|avi|mov|wmv|webm|m4v|ts)$"))return "🎬";
        if(m.startsWith("audio/")||x.matches(".*\\.(mp3|wav|flac|aac|ogg|m4a|wma)$"))return "🎵";
        if(x.endsWith(".apk")||m.contains("android.package"))return "📦";
        if(x.endsWith(".pdf")||m.contains("pdf"))return "📕";
        if(x.matches(".*\\.(zip|rar|7z|tar|gz|bz2|xz)$")||m.contains("zip")||m.contains("compressed"))return "🗜️";
        if(x.matches(".*\\.(doc|docx|odt)$"))return "📝";
        if(x.matches(".*\\.(xls|xlsx|ods|csv)$"))return "📊";
        if(x.matches(".*\\.(ppt|pptx|odp)$"))return "📽️";
        return "📄";
    }'''
if old_icon not in s:
    raise SystemExit("Método icon original não encontrado")
s=s.replace(old_icon,new_icon,1)

p.write_text(s)

# ---------- APPS ACTIVITY: escolher pasta ao extrair ----------
a = Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/AppsActivity.java")
x = a.read_text()

# campos
needle = '    boolean showSystem=false; volatile boolean loading=false;\n'
insert = '''    boolean showSystem=false; volatile boolean loading=false;
    static final int REQ_SAVE_APP_FOLDER = 7611;
    AppItem pendingSaveApp = null;
'''
if needle not in x:
    raise SystemExit("campos AppsActivity não encontrados")
x = x.replace(needle, insert, 1)

# menu
old_menu = '''ArrayList<String> o=new ArrayList<>();o.add("Extrair APK");if(a.splits.length>0)o.add("Backup completo (base + splits)");o.add("Extrair e enviar ao USB");o.add("Detalhes");'''
new_menu = '''ArrayList<String> o=new ArrayList<>();o.add("Extrair APK");o.add("Extrair e escolher pasta no celular");if(a.splits.length>0)o.add("Backup completo (base + splits)");o.add("Extrair e enviar ao USB");o.add("Detalhes");'''
if old_menu not in x:
    raise SystemExit("menu de apps não encontrado")
x = x.replace(old_menu, new_menu, 1)

old_action = '''if(s.equals("Extrair APK"))extractMany(Collections.singletonList(a),false,false);else if(s.startsWith("Backup"))extractMany(Collections.singletonList(a),false,true);else if(s.startsWith("Extrair e"))extractMany(Collections.singletonList(a),true,true);else details(a);'''
new_action = '''if(s.equals("Extrair APK"))extractMany(Collections.singletonList(a),false,false);else if(s.equals("Extrair e escolher pasta no celular"))chooseSaveFolder(a);else if(s.startsWith("Backup"))extractMany(Collections.singletonList(a),false,true);else if(s.startsWith("Extrair e enviar"))extractMany(Collections.singletonList(a),true,true);else details(a);'''
if old_action not in x:
    raise SystemExit("ação do menu não encontrada")
x = x.replace(old_action, new_action, 1)

# insere métodos antes de extractMany
marker2 = '    void extractMany(List<AppItem> src,boolean toUsb,boolean full){'
methods2 = r'''    void chooseSaveFolder(AppItem app) {
        pendingSaveApp = app;
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION |
                   Intent.FLAG_GRANT_WRITE_URI_PERMISSION |
                   Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION |
                   Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
        startActivityForResult(i, REQ_SAVE_APP_FOLDER);
    }

    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data) {
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode != REQ_SAVE_APP_FOLDER) return;
        if(resultCode != RESULT_OK || data == null || data.getData() == null || pendingSaveApp == null) {
            pendingSaveApp = null;
            return;
        }
        Uri tree = data.getData();
        try {
            int flags = data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            getContentResolver().takePersistableUriPermission(tree, flags);
        } catch(Exception ignored) {}

        AppItem app = pendingSaveApp;
        pendingSaveApp = null;
        saveInstalledAppToChosenFolder(app, tree);
    }

    void saveInstalledAppToChosenFolder(AppItem app,Uri tree) {
        ProgressDialog pd=new ProgressDialog(this);
        pd.setTitle("Salvando APK");
        pd.setMessage(app.name);
        pd.setIndeterminate(true);
        pd.setCancelable(false);
        pd.show();

        io.execute(()->{
            boolean ok=false;
            String error=null;
            try {
                String rootId=DocumentsContract.getTreeDocumentId(tree);
                Uri targetParent=DocumentsContract.buildDocumentUriUsingTree(tree,rootId);

                if(app.splits.length==0) {
                    saveSourceFileToTree(new File(app.base), targetParent, safe(app.name)+".apk");
                } else {
                    Uri folder=DocumentsContract.createDocument(
                        getContentResolver(),
                        targetParent,
                        DocumentsContract.Document.MIME_TYPE_DIR,
                        safe(app.name)+"_SPLIT"
                    );
                    if(folder==null) throw new IOException("Não foi possível criar a pasta do backup");
                    saveSourceFileToTree(new File(app.base), folder, safe(app.name)+"_base.apk");
                    for(int i=0;i<app.splits.length;i++){
                        File src=new File(app.splits[i]);
                        String name=src.getName();
                        if(!name.toLowerCase(Locale.ROOT).endsWith(".apk")) name="split_"+(i+1)+".apk";
                        saveSourceFileToTree(src, folder, name);
                    }
                }
                ok=true;
            } catch(Exception e) {
                error=e.getMessage();
            }
            boolean done=ok; String msg=error;
            runOnUiThread(()->{
                pd.dismiss();
                if(done) toast(app.splits.length==0 ? app.name+".apk salvo na pasta escolhida." : "Backup completo de "+app.name+" salvo na pasta escolhida.");
                else new AlertDialog.Builder(this).setTitle("Não foi possível salvar").setMessage(msg==null?"O Android não liberou a gravação nessa pasta.":msg).setPositiveButton("OK",null).show();
            });
        });
    }

    void saveSourceFileToTree(File source,Uri parent,String displayName)throws Exception{
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
    }

'''
if marker2 not in x:
    raise SystemExit("marker extractMany não encontrado")
x = x.replace(marker2, methods2 + marker2, 1)

a.write_text(x)

# versão
g = Path("buildsrc/app/build.gradle")
gs = g.read_text().replace('versionCode 8','versionCode 9').replace("versionName '6.0.0'","versionName '6.1.0'")
g.write_text(gs)
