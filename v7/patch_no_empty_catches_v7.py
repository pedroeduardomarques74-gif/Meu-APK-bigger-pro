from pathlib import Path
import re

configs=[
 ("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java","MainActivity","RECOVERY"),
 ("buildsrc/app/src/main/java/com/grupobigger/biggerotg/AppsActivity.java","AppsActivity","RECOVERY"),
 ("buildsrc/app/src/main/java/com/grupobigger/biggerotg/ShareReceiverActivity.java","ShareReceiverActivity","RECOVERY"),
]
for path,cls,tag in configs:
    p=Path(path); s=p.read_text()
    pattern=r'catch\s*\(\s*(Exception|Throwable)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*\{\s*\}'
    def repl(m):
        typ,var=m.group(1),m.group(2)
        return f'catch({typ} {var}){{ BiggerApp.logNonFatal({cls}.this,"{tag}","Exceção recuperada", {var}); }}'
    s,n=re.subn(pattern,repl,s)
    p.write_text(s)
    print(path,n)
