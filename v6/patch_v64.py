from pathlib import Path

p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java")
s=p.read_text()

# 1) Substitui captura de compartilhamento por importação segura
start=s.find('    void captureSharedIntent(Intent intent) {')
end=s.find('\n    Uri getSharedUri(Intent intent) {',start)
if start<0 or end<0:
    raise SystemExit("captureSharedIntent não encontrado")

new_capture=r'''    void captureSharedIntent(Intent intent) {
        if (intent == null) return;
        try {
            String action = intent.getAction();
            if (Intent.ACTION_SEND.equals(action)) {
                Uri u = getSharedUri(intent);
                if (u != null) importSharedUriSafely(u);
            } else if (Intent.ACTION_SEND_MULTIPLE.equals(action)) {
                ArrayList<Uri> list = null;
                if (Build.VERSION.SDK_INT >= 33) list = intent.getParcelableArrayListExtra(Intent.EXTRA_STREAM, Uri.class);
                else list = intent.getParcelableArrayListExtra(Intent.EXTRA_STREAM);
                if (list != null) for (Uri u : list) if (u != null) importSharedUriSafely(u);
            }
        } catch (Throwable ignored) {
        } finally {
            // Impede que o mesmo compartilhamento do Chrome seja processado novamente ao reabrir o app.
            try {
                intent.setAction(null);
                intent.removeExtra(Intent.EXTRA_STREAM);
                intent.setClipData(null);
            } catch (Throwable ignored) {}
        }
    }

    void importSharedUriSafely(Uri source) {
        if (source == null) return;
        final String key = source.toString();
        io.execute(() -> {
            try {
                String name = sharedDisplayName(source);
                if (name == null || name.trim().isEmpty()) name = "arquivo_recebido";
                name = sanitizeIncomingName(name);

                java.io.File dir = new java.io.File(getCacheDir(), "shared_incoming");
                if (!dir.exists()) dir.mkdirs();

                java.io.File outFile = uniqueIncomingFile(dir, name);
                try (InputStream in = getContentResolver().openInputStream(source);
                     OutputStream out = new java.io.FileOutputStream(outFile)) {
                    if (in == null) throw new java.io.IOException("Arquivo compartilhado indisponível");
                    byte[] buf = new byte[262144];
                    int r;
                    while ((r = in.read(buf)) > 0) out.write(buf, 0, r);
                    out.flush();
                }

                Uri local = Uri.fromFile(outFile);
                runOnUiThread(() -> {
                    try {
                        if (!pendingSharedUris.contains(local)) pendingSharedUris.add(local);
                        if (!wizardVisible) applyPendingSharedFiles();
                    } catch (Throwable ignored) {}
                });
            } catch (Throwable e) {
                runOnUiThread(() -> toast("Não foi possível importar o arquivo compartilhado."));
            }
        });
    }

    String sharedDisplayName(Uri uri) {
        if (uri == null) return null;
        try {
            if ("file".equalsIgnoreCase(uri.getScheme())) {
                java.io.File f = new java.io.File(uri.getPath());
                return f.getName();
            }
            try (Cursor c = getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
                if (c != null && c.moveToFirst()) {
                    int i = c.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                    if (i >= 0) return c.getString(i);
                }
            }
        } catch (Throwable ignored) {}
        String last = uri.getLastPathSegment();
        return last == null ? "arquivo_recebido" : last;
    }

    String sanitizeIncomingName(String name) {
        String clean = name.replaceAll("[\\\\/:*?\"<>|]", "_").trim();
        return clean.isEmpty() ? "arquivo_recebido" : clean;
    }

    java.io.File uniqueIncomingFile(java.io.File dir, String name) {
        java.io.File f = new java.io.File(dir, name);
        if (!f.exists()) return f;
        String base = name, ext = "";
        int dot = name.lastIndexOf('.');
        if (dot > 0) { base = name.substring(0, dot); ext = name.substring(dot); }
        for (int i = 2; ; i++) {
            f = new java.io.File(dir, base + " (" + i + ")" + ext);
            if (!f.exists()) return f;
        }
    }

'''
s=s[:start]+new_capture+s[end:]

# 2) Não tenta criar View/Drawable no worker thread quando falhar miniatura.
old='''            if(found==null)found=fallbackDrawableFor(n);
            fileVisualCache.put(key,found);
            fileVisualLoading.remove(key);
            android.graphics.drawable.Drawable result=found;
            runOnUiThread(()->{
                Object tag=tv.getTag();
                if(tag!=null&&key.equals(tag.toString()))setCompoundApkIcon(tv,result,n.name);
            });'''
new='''            fileVisualLoading.remove(key);
            android.graphics.drawable.Drawable result=found;
            if(result!=null) fileVisualCache.put(key,result);
            runOnUiThread(()->{
                Object tag=tv.getTag();
                if(tag!=null&&key.equals(tag.toString())){
                    if(result!=null) setCompoundApkIcon(tv,result,n.name);
                    else tv.setText(icon(n)+"  "+n.name);
                }
            });'''
if old not in s:
    raise SystemExit("bloco fallback async não encontrado")
s=s.replace(old,new,1)

# 3) Protege importação pendente contra qualquer Throwable
old='''        for (Uri u : new ArrayList<>(pendingSharedUris)) {
            try { Node n = nodeFromSharedUri(u); if (n != null) incoming.add(n); } catch (Exception ignored) {}
        }'''
new='''        for (Uri u : new ArrayList<>(pendingSharedUris)) {
            try { Node n = nodeFromSharedUri(u); if (n != null) incoming.add(n); } catch (Throwable ignored) {}
        }'''
if old in s:
    s=s.replace(old,new,1)

# 4) Limpa o Intent da Activity logo após capturar, inclusive no onCreate/onNewIntent.
s=s.replace('captureSharedIntent(getIntent());\n        captureExtractedPaths(getIntent());',
'''captureSharedIntent(getIntent());
        captureExtractedPaths(getIntent());
        try { setIntent(new Intent(this, MainActivity.class)); } catch (Throwable ignored) {}''',1)

s=s.replace('captureSharedIntent(intent);\n        captureExtractedPaths(intent);',
'''captureSharedIntent(intent);
        captureExtractedPaths(intent);
        try { setIntent(new Intent(this, MainActivity.class)); } catch (Throwable ignored) {}''',1)

p.write_text(s)

# versão
b=Path("buildsrc/app/build.gradle")
g=b.read_text().replace('versionCode 11','versionCode 12').replace("versionName '6.3.0'","versionName '6.4.0'")
b.write_text(g)
