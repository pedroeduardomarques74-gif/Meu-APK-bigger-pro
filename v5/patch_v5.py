from pathlib import Path

p=Path('buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java')
s=p.read_text()

s=s.replace('captureSharedIntent(getIntent());\n        if (!wizardVisible) applyPendingSharedFiles();',
'''captureSharedIntent(getIntent());
        captureExtractedPaths(getIntent());
        if (!wizardVisible) applyPendingSharedFiles();''')

s=s.replace('captureSharedIntent(intent);\n        if (!wizardVisible) applyPendingSharedFiles();',
'''captureSharedIntent(intent);
        captureExtractedPaths(intent);
        if (!wizardVisible) applyPendingSharedFiles();''')

marker='    void captureSharedIntent(Intent intent) {'
methods='''    void captureExtractedPaths(Intent intent) {
        if (intent == null) return;
        ArrayList<String> paths = intent.getStringArrayListExtra("bigger_extracted_paths");
        if (paths == null) return;
        for (String path : paths) {
            if (path == null) continue;
            Uri u = Uri.fromFile(new java.io.File(path));
            if (!pendingSharedUris.contains(u)) pendingSharedUris.add(u);
        }
        intent.removeExtra("bigger_extracted_paths");
    }

'''
s=s.replace(marker,methods+marker)

old='''        LinearLayout quick = horizontal();
        Button reconnect = button("↻  DETECTAR / ABRIR OTG", BLUE);
        reconnect.setOnClickListener(v -> autoConnectUsb(true));
        quick.addView(reconnect, weight()); root.addView(quick);'''
new='''        LinearLayout quick = horizontal();
        Button reconnect = button("↻  DETECTAR / ABRIR OTG", BLUE);
        reconnect.setOnClickListener(v -> autoConnectUsb(true));
        Button apps = button("📦  APPS INSTALADOS", PANEL2);
        apps.setOnClickListener(v -> startActivity(new Intent(MainActivity.this, AppsActivity.class)));
        quick.addView(reconnect, weight()); quick.addView(apps, weight()); root.addView(quick);'''
s=s.replace(old,new)
p.write_text(s)

m=Path('buildsrc/app/src/main/AndroidManifest.xml')
ms=m.read_text()
if 'QUERY_ALL_PACKAGES' not in ms:
    ms=ms.replace('<uses-feature android:name="android.hardware.usb.host" android:required="false" />',
                  '<uses-feature android:name="android.hardware.usb.host" android:required="false" />\n    <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" />')
if 'AppsActivity' not in ms:
    ms=ms.replace('<activity android:name=".MainActivity"',
                  '<activity android:name=".AppsActivity" android:exported="false" />\n        <activity android:name=".MainActivity"')
m.write_text(ms)

src=Path('v5/AppsActivity.java')
dst=Path('buildsrc/app/src/main/java/com/grupobigger/biggerotg/AppsActivity.java')
dst.write_text(src.read_text())

b=Path('buildsrc/app/build.gradle')
bs=b.read_text().replace('versionCode 4','versionCode 5').replace("versionName '4.0.0'","versionName '5.0.0'")
b.write_text(bs)
