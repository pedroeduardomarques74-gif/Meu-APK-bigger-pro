from pathlib import Path

for fp in [
    Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java"),
    Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/AppsActivity.java")
]:
    s=fp.read_text()
    s=s.replace('''!"content".equalsIgnoreCase(u.getScheme()) || !DocumentsContract.isTreeUri(u)''',
                '''!"content".equalsIgnoreCase(u.getScheme()) || (Build.VERSION.SDK_INT>=24 && !DocumentsContract.isTreeUri(u))''')
    s=s.replace('''!"content".equalsIgnoreCase(u.getScheme())||!DocumentsContract.isTreeUri(u)''',
                '''!"content".equalsIgnoreCase(u.getScheme())||(Build.VERSION.SDK_INT>=24&&!DocumentsContract.isTreeUri(u))''')
    fp.write_text(s)
