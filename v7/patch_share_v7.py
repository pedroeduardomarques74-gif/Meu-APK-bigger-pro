from pathlib import Path

p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/ShareReceiverActivity.java")
s=p.read_text()

s=s.replace('''public class ShareReceiverActivity extends Activity {
    LinearLayout root;
    TextView status;''','''public class ShareReceiverActivity extends Activity {
    LinearLayout root;
    TextView status;
    final java.util.concurrent.ExecutorService io=java.util.concurrent.Executors.newSingleThreadExecutor();
    volatile boolean destroyed=false;''',1)

s=s.replace('''    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        buildUi();
        handleShare(getIntent());
    }''','''    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        BiggerApp.markAction(this,"SHARE_INTENT");
        buildUi();
        handleShare(getIntent());
    }

    @Override protected void onDestroy(){
        destroyed=true;
        io.shutdownNow();
        super.onDestroy();
    }

    boolean alive(){
        if(destroyed||isFinishing())return false;
        return Build.VERSION.SDK_INT<17||!isDestroyed();
    }

    void safeUi(Runnable r){
        runOnUiThread(()->{if(!alive())return;try{r.run();}catch(Throwable e){BiggerApp.logNonFatal(this,"SHARE_INTENT","UI",e);}});
    }''',1)

# handle share with executor and generic message
start=s.find('    void handleShare(Intent intent) {')
end=s.find('\n    ArrayList<Uri> collectUris',start)
if start<0 or end<0: raise SystemExit("handleShare")
newhandle=r'''    void handleShare(Intent intent) {
        io.execute(() -> {
            try {
                ArrayList<Uri> uris = collectUris(intent);
                if (uris.isEmpty()) throw new IOException("Nenhum arquivo recebido");

                ArrayList<String> paths = new ArrayList<>();
                int total = uris.size();
                for (int i=0;i<uris.size();i++) {
                    if(Thread.currentThread().isInterrupted())throw new InterruptedIOException("Operação cancelada");
                    final int n=i+1;
                    safeUi(() -> status.setText(total==1 ? "Importando arquivo..." : "Importando "+n+" de "+total+"..."));
                    File f = copyUriToPrivateCache(uris.get(i));
                    if (f != null && f.exists() && f.length() > 0) paths.add(f.getAbsolutePath());
                }

                if (paths.isEmpty()) throw new IOException("Não foi possível copiar o arquivo");

                safeUi(() -> {
                    try{
                        Intent open = new Intent(ShareReceiverActivity.this, MainActivity.class);
                        open.putStringArrayListExtra("bigger_extracted_paths", paths);
                        open.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                        startActivity(open);
                        finish();
                    }catch(Throwable e){
                        BiggerApp.logNonFatal(this,"SHARE_INTENT","Abrir MainActivity",e);
                        status.setText("Arquivo recebido, mas não foi possível abrir a tela principal.");
                    }
                });
            } catch (Throwable e) {
                BiggerApp.logNonFatal(this,"SHARE_INTENT","Falha ao receber arquivo",e);
                safeUi(() -> {
                    status.setText("Não foi possível receber esse arquivo.");
                    Toast.makeText(this,"Falha ao receber o arquivo compartilhado.",Toast.LENGTH_LONG).show();
                    new Handler(Looper.getMainLooper()).postDelayed(() -> {
                        if(!alive())return;
                        try {
                            Intent open = new Intent(this, MainActivity.class);
                            open.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                            startActivity(open);
                        } catch (Throwable ex) { BiggerApp.logNonFatal(this,"SHARE_INTENT","Recuperação",ex); }
                        finish();
                    },1200);
                });
            }
        });
    }

'''
s=s[:start]+newhandle+s[end:]

# collect Uris: combina EXTRA_STREAM, ClipData e ACTION_VIEW sem duplicar
start=s.find('    ArrayList<Uri> collectUris(Intent intent) {')
end=s.find('\n    File copyUriToPrivateCache',start)
newcollect=r'''    ArrayList<Uri> collectUris(Intent intent) {
        LinkedHashSet<Uri> set=new LinkedHashSet<>();
        if (intent == null) return new ArrayList<>();
        try {
            String action=intent.getAction();
            if (Intent.ACTION_SEND.equals(action)) {
                Uri u=Build.VERSION.SDK_INT>=33?intent.getParcelableExtra(Intent.EXTRA_STREAM,Uri.class):intent.getParcelableExtra(Intent.EXTRA_STREAM);
                if(u!=null)set.add(u);
            } else if (Intent.ACTION_SEND_MULTIPLE.equals(action)) {
                ArrayList<Uri> list=Build.VERSION.SDK_INT>=33?intent.getParcelableArrayListExtra(Intent.EXTRA_STREAM,Uri.class):intent.getParcelableArrayListExtra(Intent.EXTRA_STREAM);
                if(list!=null)for(Uri u:list)if(u!=null)set.add(u);
            } else if(Intent.ACTION_VIEW.equals(action) && intent.getData()!=null){
                set.add(intent.getData());
            }
            if(intent.getClipData()!=null){
                for(int i=0;i<intent.getClipData().getItemCount();i++){
                    Uri u=intent.getClipData().getItemAt(i).getUri();if(u!=null)set.add(u);
                }
            }
            if(set.isEmpty()&&intent.getData()!=null)set.add(intent.getData());
        } catch (Throwable e) { BiggerApp.logNonFatal(this,"SHARE_INTENT","Ler Intent",e); }
        return new ArrayList<>(set);
    }

'''
s=s[:start]+newcollect+s[end:]

# cópia robusta, nome limitado e espaço
start=s.find('    File copyUriToPrivateCache(Uri uri) throws Exception {')
end=s.find('\n    String displayName',start)
newcopy=r'''    File copyUriToPrivateCache(Uri uri) throws Exception {
        if(uri==null)throw new FileNotFoundException("URI vazia");
        String name = sanitizeName(displayName(uri));

        File dir = new File(getCacheDir(),"shared_incoming");
        if (!dir.exists() && !dir.mkdirs()) throw new IOException("Falha ao preparar pasta");

        long expected=querySize(uri);
        if(expected>0 && dir.getUsableSpace()>0 && dir.getUsableSpace()<expected+5*1024*1024L)throw new IOException("Espaço insuficiente");

        File out = uniqueFile(dir,name);
        try (InputStream raw = getContentResolver().openInputStream(uri)) {
            if(raw==null)throw new IOException("Arquivo indisponível");
            try(InputStream in=new BufferedInputStream(raw);OutputStream os=new BufferedOutputStream(new FileOutputStream(out))){
                byte[] buf = new byte[128*1024];
                int r;
                while ((r=in.read(buf)) > 0) {
                    if(Thread.currentThread().isInterrupted())throw new InterruptedIOException("Operação cancelada");
                    os.write(buf,0,r);
                }
                os.flush();
            }
        }catch(Throwable e){
            try{out.delete();}catch(Throwable ignored){}
            if(e instanceof Exception)throw (Exception)e;
            throw new IOException(e);
        }
        if(!out.exists()||out.length()<=0)throw new IOException("Arquivo recebido vazio");
        return out;
    }

    long querySize(Uri uri){
        try(Cursor c=getContentResolver().query(uri,new String[]{OpenableColumns.SIZE},null,null,null)){
            if(c!=null&&c.moveToFirst()){int i=c.getColumnIndex(OpenableColumns.SIZE);if(i>=0&&!c.isNull(i))return c.getLong(i);}
        }catch(Throwable e){BiggerApp.logNonFatal(this,"SHARE_INTENT","Consultar tamanho",e);}
        return -1;
    }

    String sanitizeName(String name){
        String clean=name==null?"arquivo_recebido":name.replaceAll("[\\\\/:*?\"<>|]","_").trim();
        if(clean.isEmpty())clean="arquivo_recebido";
        if(clean.length()>160){
            String ext="";int dot=clean.lastIndexOf('.');
            if(dot>0&&clean.length()-dot<=12){ext=clean.substring(dot);clean=clean.substring(0,Math.min(dot,160-ext.length()))+ext;}
            else clean=clean.substring(0,160);
        }
        return clean;
    }

'''
s=s[:start]+newcopy+s[end:]

# displayName logs
s=s.replace('''        } catch (Throwable ignored) {}''','''        } catch (Throwable e) { BiggerApp.logNonFatal(this,"SHARE_INTENT","Nome do arquivo",e); }''',1)

p.write_text(s)
