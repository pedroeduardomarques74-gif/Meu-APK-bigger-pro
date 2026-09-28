from pathlib import Path
p=Path('buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java')
s=p.read_text()
s=s.replace('import android.provider.DocumentsContract;', 'import android.provider.DocumentsContract;\nimport android.provider.OpenableColumns;')
s=s.replace('long lastAutoPrompt = 0L;', 'long lastAutoPrompt = 0L;\n    final ArrayList<Uri> pendingSharedUris = new ArrayList<>();')
s=s.replace('if (prefs.getBoolean("setup_done", false)) showMainUi(); else showSetupWizard();\n        new Handler', 'if (prefs.getBoolean("setup_done", false)) showMainUi(); else showSetupWizard();\n        captureSharedIntent(getIntent());\n        if (!wizardVisible) applyPendingSharedFiles();\n        new Handler')
s=s.replace('refreshUsbStatus();\n        if (UsbManager.ACTION_USB_DEVICE_ATTACHED.equals(intent.getAction())) {', 'refreshUsbStatus();\n        captureSharedIntent(intent);\n        if (!wizardVisible) applyPendingSharedFiles();\n        if (UsbManager.ACTION_USB_DEVICE_ATTACHED.equals(intent.getAction())) {')
marker='    void showMainUi() {'
methods=r'''
    void captureSharedIntent(Intent intent) {
        if (intent == null) return;
        String action = intent.getAction();
        if (Intent.ACTION_SEND.equals(action)) {
            Uri u = getSharedUri(intent);
            if (u != null && !pendingSharedUris.contains(u)) pendingSharedUris.add(u);
        } else if (Intent.ACTION_SEND_MULTIPLE.equals(action)) {
            ArrayList<Uri> list = null;
            if (Build.VERSION.SDK_INT >= 33) list = intent.getParcelableArrayListExtra(Intent.EXTRA_STREAM, Uri.class);
            else list = intent.getParcelableArrayListExtra(Intent.EXTRA_STREAM);
            if (list != null) for (Uri u : list) if (u != null && !pendingSharedUris.contains(u)) pendingSharedUris.add(u);
        }
    }

    Uri getSharedUri(Intent intent) {
        try {
            if (Build.VERSION.SDK_INT >= 33) return intent.getParcelableExtra(Intent.EXTRA_STREAM, Uri.class);
            return intent.getParcelableExtra(Intent.EXTRA_STREAM);
        } catch (Exception e) { return null; }
    }

    void applyPendingSharedFiles() {
        if (phone == null || pendingSharedUris.isEmpty()) return;
        ArrayList<Node> incoming = new ArrayList<>();
        for (Uri u : new ArrayList<>(pendingSharedUris)) {
            try { Node n = nodeFromSharedUri(u); if (n != null) incoming.add(n); } catch (Exception ignored) {}
        }
        if (incoming.isEmpty()) return;
        phone.showIncoming(incoming);
        pendingSharedUris.clear();
        toast(incoming.size() == 1 ? "Arquivo recebido e selecionado." : incoming.size()+" arquivos recebidos e selecionados.");
    }

    Node nodeFromSharedUri(Uri u) {
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
    }

'''
s=s.replace(marker,methods+marker)
s=s.replace('restoreRoots();\n        refreshUsbStatus();\n    }', 'restoreRoots();\n        refreshUsbStatus();\n        applyPendingSharedFiles();\n    }', 1)
s=s.replace('void setRoot(Uri uri){ treeUri=uri; rootDocId=DocumentsContract.getTreeDocumentId(uri); currentDocId=rootDocId; stack.clear(); selected.clear(); load(); }', 'void setRoot(Uri uri){ treeUri=uri; rootDocId=DocumentsContract.getTreeDocumentId(uri); currentDocId=rootDocId; stack.clear(); selected.clear(); load(); }\n        void showIncoming(List<Node> nodes){ if(isUsb)return; currentNodes=new ArrayList<>(nodes); selected.clear(); for(Node n:nodes)selected.put(n.id,n); path.setText("📥 Recebido pelo Compartilhar • pronto para copiar ao USB"); search.setText(""); render(); }')
s=s.replace('Button more=mini("⋮"); more.setOnClickListener(v->fileMenu(n)); r.addView(more);', 'Button more=mini("⋮"); if(n.externalUri!=null){more.setEnabled(false); more.setAlpha(0.35f);} else more.setOnClickListener(v->fileMenu(n)); r.addView(more);')
s=s.replace('    void transfer(Pane src, Pane dst, boolean move){', '    boolean hasExternalSelection(Pane pane){ for(Node n:pane.selected.values()) if(n.externalUri!=null) return true; return false; }\n\n    void transfer(Pane src, Pane dst, boolean move){', 1)
s=s.replace('if(src.treeUri==null||dst.treeUri==null){toast("Abra o celular e o USB primeiro.");return;}', 'if(dst.treeUri==null || (src.treeUri==null && !hasExternalSelection(src))){toast("Abra o celular e o USB primeiro.");return;}', 1)
s=s.replace('if(copied){ok++; if(move)try{DocumentsContract.deleteDocument(getContentResolver(),docUri(src.treeUri,n.id));}catch(Exception ignored){}}', 'if(copied){ok++; if(move)try{ if(n.externalUri!=null) DocumentsContract.deleteDocument(getContentResolver(),n.externalUri); else DocumentsContract.deleteDocument(getContentResolver(),docUri(src.treeUri,n.id)); }catch(Exception ignored){}}', 1)
s=s.replace('try(InputStream in=getContentResolver().openInputStream(docUri(srcTree,source.id)); OutputStream out=getContentResolver().openOutputStream(made,"w")){', 'Uri sourceUri = source.externalUri != null ? source.externalUri : docUri(srcTree,source.id);\n            try(InputStream in=getContentResolver().openInputStream(sourceUri); OutputStream out=getContentResolver().openOutputStream(made,"w")){', 1)
s=s.replace('static class Node{String id,name,mime;boolean dir;long size,modified;}', 'static class Node{String id,name,mime;boolean dir;long size,modified;Uri externalUri;}')
p.write_text(s)

m=Path('buildsrc/app/src/main/AndroidManifest.xml')
ms=m.read_text()
extra='''\n            <intent-filter>\n                <action android:name="android.intent.action.SEND" />\n                <category android:name="android.intent.category.DEFAULT" />\n                <data android:mimeType="*/*" />\n            </intent-filter>\n            <intent-filter>\n                <action android:name="android.intent.action.SEND_MULTIPLE" />\n                <category android:name="android.intent.category.DEFAULT" />\n                <data android:mimeType="*/*" />\n            </intent-filter>'''
ms=ms.replace('            <intent-filter>\n                <action android:name="android.hardware.usb.action.USB_DEVICE_ATTACHED" />\n            </intent-filter>', '            <intent-filter>\n                <action android:name="android.hardware.usb.action.USB_DEVICE_ATTACHED" />\n            </intent-filter>'+extra)
m.write_text(ms)

b=Path('buildsrc/app/build.gradle')
b.write_text(b.read_text().replace('versionCode 3','versionCode 4').replace("versionName '3.0.0'","versionName '4.0.0'"))
