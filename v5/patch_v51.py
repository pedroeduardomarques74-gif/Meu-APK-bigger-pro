from pathlib import Path

# MainActivity: debounce Apps Installed button
p=Path('buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java')
s=p.read_text()
old='''Button apps = button("📦  APPS INSTALADOS", PANEL2);
        apps.setOnClickListener(v -> startActivity(new Intent(MainActivity.this, AppsActivity.class)));'''
new='''Button apps = button("📦  APPS INSTALADOS", PANEL2);
        apps.setOnClickListener(v -> {
            if (!v.isEnabled()) return;
            v.setEnabled(false);
            startActivity(new Intent(MainActivity.this, AppsActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP));
            v.postDelayed(() -> v.setEnabled(true), 1200);
        });'''
s=s.replace(old,new)
p.write_text(s)

# Manifest: singleTop for AppsActivity
m=Path('buildsrc/app/src/main/AndroidManifest.xml')
ms=m.read_text().replace('<activity android:name=".AppsActivity" android:exported="false" />',
                         '<activity android:name=".AppsActivity" android:exported="false" android:launchMode="singleTop" />')
m.write_text(ms)

# Replace AppsActivity with lightweight ListView implementation
src=Path('v5/AppsActivity_v51.java')
dst=Path('buildsrc/app/src/main/java/com/grupobigger/biggerotg/AppsActivity.java')
dst.write_text(src.read_text())

b=Path('buildsrc/app/build.gradle')
bs=b.read_text().replace('versionCode 5','versionCode 6').replace("versionName '5.0.0'","versionName '5.1.0'")
b.write_text(bs)
