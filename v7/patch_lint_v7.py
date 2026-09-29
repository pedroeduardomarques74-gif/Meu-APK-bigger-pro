from pathlib import Path
import re

# BiggerApp: Comparator compatível com API 21
p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/BiggerApp.java")
s=p.read_text()
s=s.replace('Arrays.sort(fs,Comparator.comparingLong(File::lastModified).reversed());',
'''Arrays.sort(fs,new Comparator<File>(){
                @Override public int compare(File a,File b){return Long.compare(b.lastModified(),a.lastModified());}
            });''')
p.write_text(s)

# MainActivity
p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java")
s=p.read_text()

# Todas as chamadas isTreeUri só em API >=24
s=re.sub(r'!DocumentsContract\.isTreeUri\(([^)]+)\)',
         r'(Build.VERSION.SDK_INT>=24&&!DocumentsContract.isTreeUri(\1))',s)

# StorageVolume.getDescription só API 24+
s=s.replace('volume.getDescription(this)',
            '(Build.VERSION.SDK_INT>=24?volume.getDescription(this):"USB / OTG")')
s=s.replace('v.getDescription(this)',
            '(Build.VERSION.SDK_INT>=24?v.getDescription(this):"USB / OTG")')

# Receiver customizado com flag quando overload está disponível
old='''            if (Build.VERSION.SDK_INT >= 33) registerReceiver(usbReceiver, f, Context.RECEIVER_NOT_EXPORTED);
            else registerReceiver(usbReceiver, f);'''
new='''            if (Build.VERSION.SDK_INT >= 26) registerReceiver(usbReceiver, f, Context.RECEIVER_NOT_EXPORTED);
            else registerReceiver(usbReceiver, f);'''
s=s.replace(old,new)

# URI permission: somente READ/WRITE são aceitos por takePersistableUriPermission
s=re.sub(r'int flags\s*=\s*data\.getFlags\(\)\s*&\s*\([^;]+\);',
'''int flags = data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);''',s)

# Typeface constants
s=s.replace('setTypeface(null,1)','setTypeface(null,android.graphics.Typeface.BOLD)')
p.write_text(s)

# AppsActivity
p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/AppsActivity.java")
s=p.read_text()
s=re.sub(r'!DocumentsContract\.isTreeUri\(([^)]+)\)',
         r'(Build.VERSION.SDK_INT>=24&&!DocumentsContract.isTreeUri(\1))',s)
s=re.sub(r'int flags\s*=\s*data\.getFlags\(\)\s*&\s*\([^;]+\);',
'''int flags = data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);''',s)
s=s.replace('setTypeface(null,1)','setTypeface(null,android.graphics.Typeface.BOLD)')
p.write_text(s)

# Share receiver Typeface
p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/ShareReceiverActivity.java")
s=p.read_text().replace('setTypeface(null,1)','setTypeface(null,android.graphics.Typeface.BOLD)')
p.write_text(s)

# style API 23: não precisa dessa flag para o tema escuro atual
p=Path("buildsrc/app/src/main/res/values/styles.xml")
s=p.read_text()
s=re.sub(r'\s*<item name="android:windowLightStatusBar">[^<]*</item>','',s)
p.write_text(s)

# QUERY_ALL_PACKAGES é requisito funcional para tela de extração de todos os apps.
p=Path("buildsrc/app/src/main/AndroidManifest.xml")
s=p.read_text()
if 'xmlns:tools=' not in s:
    s=s.replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android"',
                '<manifest xmlns:android="http://schemas.android.com/apk/res/android" xmlns:tools="http://schemas.android.com/tools"')
s=s.replace('<uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" />',
            '<uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" tools:ignore="QueryAllPackagesPermission" />')
p.write_text(s)


# Suprimir somente falsos positivos validados de flags, mantendo compatibilidade antiga.
for fp, cls in [
    (Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java"),"MainActivity"),
    (Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/AppsActivity.java"),"AppsActivity")
]:
    x=fp.read_text()
    # Encapsula calls de takePersistableUriPermission em helper anotado.
    x=x.replace("getContentResolver().takePersistableUriPermission(tree, flags);",
                "takePersistablePermissionChecked(tree, flags);")
    x=x.replace("getContentResolver().takePersistableUriPermission(uri, flags);",
                "takePersistablePermissionChecked(uri, flags);")
    marker="    int dp(int v)"
    helper='''    @android.annotation.SuppressLint("WrongConstant")
    void takePersistablePermissionChecked(Uri uri,int flags){
        int allowed=flags & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
        if(allowed!=0)getContentResolver().takePersistableUriPermission(uri,allowed);
    }

'''
    if helper not in x and marker in x:x=x.replace(marker,helper+marker,1)
    fp.write_text(x)

p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java")
x=p.read_text()
x=x.replace("    void registerUsbReceiver() {",
'''    @android.annotation.SuppressLint("UnspecifiedRegisterReceiverFlag")
    void registerUsbReceiver() {''',1)
p.write_text(x)
