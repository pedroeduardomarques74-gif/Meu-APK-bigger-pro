from pathlib import Path

# Copia a Activity receptora dedicada
src=Path("v6/ShareReceiverActivity.java")
dst=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/ShareReceiverActivity.java")
dst.write_text(src.read_text())

# Manifest: remove os filtros SEND da MainActivity e coloca só na ShareReceiverActivity
m=Path("buildsrc/app/src/main/AndroidManifest.xml")
s=m.read_text()

send1='''            <intent-filter>
                <action android:name="android.intent.action.SEND" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:mimeType="*/*" />
            </intent-filter>
            <intent-filter>
                <action android:name="android.intent.action.SEND_MULTIPLE" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:mimeType="*/*" />
            </intent-filter>'''
s=s.replace(send1,'')

receiver='''        <activity
            android:name=".ShareReceiverActivity"
            android:exported="true"
            android:excludeFromRecents="true"
            android:noHistory="true">
            <intent-filter>
                <action android:name="android.intent.action.SEND" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:mimeType="*/*" />
            </intent-filter>
            <intent-filter>
                <action android:name="android.intent.action.SEND_MULTIPLE" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:mimeType="*/*" />
            </intent-filter>
        </activity>
'''
if '.ShareReceiverActivity' not in s:
    s=s.replace('<activity android:name=".AppsActivity"', receiver+'        <activity android:name=".AppsActivity"',1)

m.write_text(s)

# Incrementa versão
b=Path("buildsrc/app/build.gradle")
g=b.read_text().replace('versionCode 12','versionCode 13').replace("versionName '6.4.0'","versionName '6.5.0'")
b.write_text(g)
