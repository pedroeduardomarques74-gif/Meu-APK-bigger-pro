from pathlib import Path

# Corrige leitura de arquivos locais extraídos na tela CELULAR
p=Path('buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java')
s=p.read_text()
old='''    Node nodeFromSharedUri(Uri u) {
        Node n = new Node(); n.externalUri = u; n.id = "shared:" + u; n.mime = getContentResolver().getType(u);
        if (n.mime == null) n.mime = "application/octet-stream"; n.name = "arquivo_recebido"; n.size = 0;
        try (Cursor c = getContentResolver().query(u, new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE}, null, null, null)) {
            if (c != null && c.moveToFirst()) {
                int ni=c.getColumnIndex(OpenableColumns.DISPLAY_NAME), si=c.getColumnIndex(OpenableColumns.SIZE);
                if (ni>=0 && c.getString(ni)!=null) n.name=c.getString(ni);
                if (si>=0 && !c.isNull(si)) n.size=c.getLong(si);
            }
        } catch (Exception ignored) {}
        n.dir=false; n.modified=System.currentTimeMillis(); return n;
    }'''
new='''    Node nodeFromSharedUri(Uri u) {
        Node n = new Node();
        n.externalUri = u;
        n.id = "shared:" + u;
        n.mime = getContentResolver().getType(u);
        n.name = "arquivo_recebido";
        n.size = 0;
        n.modified = System.currentTimeMillis();

        if ("file".equalsIgnoreCase(u.getScheme())) {
            try {
                java.io.File f = new java.io.File(u.getPath());
                n.name = f.getName();
                n.size = f.length();
                n.modified = f.lastModified();
                if (n.name.toLowerCase(Locale.ROOT).endsWith(".apk"))
                    n.mime = "application/vnd.android.package-archive";
            } catch (Exception ignored) {}
        } else {
            try (Cursor c = getContentResolver().query(u, new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE}, null, null, null)) {
                if (c != null && c.moveToFirst()) {
                    int ni=c.getColumnIndex(OpenableColumns.DISPLAY_NAME), si=c.getColumnIndex(OpenableColumns.SIZE);
                    if (ni>=0 && c.getString(ni)!=null) n.name=c.getString(ni);
                    if (si>=0 && !c.isNull(si)) n.size=c.getLong(si);
                }
            } catch (Exception ignored) {}
        }

        if (n.mime == null) n.mime = "application/octet-stream";
        n.dir=false;
        return n;
    }'''
if old not in s:
    raise SystemExit('Trecho nodeFromSharedUri não encontrado')
s=s.replace(old,new)
p.write_text(s)

# Nome simples: NomeDoApp.apk
a=Path('buildsrc/app/src/main/java/com/grupobigger/biggerotg/AppsActivity.java')
x=a.read_text()
old2='''if(a.splits.length==0||!full){File d=new File(root,n+"_"+v+".apk");copy(new File(a.base),d);out.add(d);return out;}'''
new2='''if(a.splits.length==0||!full){File d=new File(root,n+".apk");copy(new File(a.base),d);out.add(d);return out;}'''
if old2 not in x:
    raise SystemExit('Trecho de nome do APK não encontrado')
x=x.replace(old2,new2)
a.write_text(x)

# Incrementa versão
b=Path('buildsrc/app/build.gradle')
bs=b.read_text().replace('versionCode 6','versionCode 7').replace("versionName '5.1.0'","versionName '5.2.0'")
b.write_text(bs)
