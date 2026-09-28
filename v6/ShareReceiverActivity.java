package com.grupobigger.biggerotg;

import android.app.*;
import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.os.*;
import android.provider.OpenableColumns;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.*;

public class ShareReceiverActivity extends Activity {
    LinearLayout root;
    TextView status;

    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        buildUi();
        handleShare(getIntent());
    }

    void buildUi() {
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(dp(24),dp(24),dp(24),dp(24));
        root.setBackgroundColor(android.graphics.Color.rgb(8,17,31));

        TextView title = new TextView(this);
        title.setText("BIGGER OTG");
        title.setTextColor(android.graphics.Color.WHITE);
        title.setTextSize(24);
        title.setTypeface(null,1);
        title.setGravity(Gravity.CENTER);
        root.addView(title);

        status = new TextView(this);
        status.setText("Recebendo arquivo...");
        status.setTextColor(android.graphics.Color.rgb(156,176,198));
        status.setTextSize(15);
        status.setGravity(Gravity.CENTER);
        status.setPadding(0,dp(14),0,0);
        root.addView(status);

        ProgressBar p = new ProgressBar(this);
        LinearLayout.LayoutParams pp = new LinearLayout.LayoutParams(dp(44),dp(44));
        pp.setMargins(0,dp(18),0,0);
        root.addView(p,pp);

        setContentView(root);

        if (Build.VERSION.SDK_INT >= 30) {
            getWindow().setDecorFitsSystemWindows(true);
        }
    }

    void handleShare(Intent intent) {
        new Thread(() -> {
            try {
                ArrayList<Uri> uris = collectUris(intent);
                if (uris.isEmpty()) throw new IOException("Nenhum arquivo recebido");

                ArrayList<String> paths = new ArrayList<>();
                int total = uris.size();
                for (int i=0;i<uris.size();i++) {
                    final int n=i+1;
                    runOnUiThread(() -> status.setText(total==1 ? "Importando arquivo..." : "Importando "+n+" de "+total+"..."));
                    File f = copyUriToPrivateCache(uris.get(i));
                    if (f != null && f.exists() && f.length() > 0) paths.add(f.getAbsolutePath());
                }

                if (paths.isEmpty()) throw new IOException("Não foi possível copiar o arquivo");

                runOnUiThread(() -> {
                    Intent open = new Intent(ShareReceiverActivity.this, MainActivity.class);
                    open.putStringArrayListExtra("bigger_extracted_paths", paths);
                    open.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(open);
                    finish();
                });
            } catch (Throwable e) {
                runOnUiThread(() -> {
                    status.setText("Não foi possível receber esse arquivo.");
                    Toast.makeText(this,"Falha ao receber o arquivo do Chrome.",Toast.LENGTH_LONG).show();
                    new Handler(Looper.getMainLooper()).postDelayed(() -> {
                        try {
                            Intent open = new Intent(this, MainActivity.class);
                            open.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                            startActivity(open);
                        } catch (Throwable ignored) {}
                        finish();
                    },1200);
                });
            }
        }).start();
    }

    ArrayList<Uri> collectUris(Intent intent) {
        ArrayList<Uri> out = new ArrayList<>();
        if (intent == null) return out;
        try {
            if (Intent.ACTION_SEND.equals(intent.getAction())) {
                Uri u;
                if (Build.VERSION.SDK_INT >= 33) u = intent.getParcelableExtra(Intent.EXTRA_STREAM, Uri.class);
                else u = intent.getParcelableExtra(Intent.EXTRA_STREAM);
                if (u != null) out.add(u);
            } else if (Intent.ACTION_SEND_MULTIPLE.equals(intent.getAction())) {
                ArrayList<Uri> list;
                if (Build.VERSION.SDK_INT >= 33) list = intent.getParcelableArrayListExtra(Intent.EXTRA_STREAM, Uri.class);
                else list = intent.getParcelableArrayListExtra(Intent.EXTRA_STREAM);
                if (list != null) for (Uri u:list) if (u != null) out.add(u);
            }

            if (out.isEmpty() && intent.getClipData() != null) {
                for (int i=0;i<intent.getClipData().getItemCount();i++) {
                    Uri u = intent.getClipData().getItemAt(i).getUri();
                    if (u != null) out.add(u);
                }
            }

            if (out.isEmpty() && intent.getData() != null) out.add(intent.getData());
        } catch (Throwable ignored) {}
        return out;
    }

    File copyUriToPrivateCache(Uri uri) throws Exception {
        String name = displayName(uri);
        if (name == null || name.trim().isEmpty()) name = "arquivo_recebido";
        name = name.replaceAll("[\\/:*?\"<>|]","_").trim();

        File dir = new File(getCacheDir(),"shared_incoming");
        if (!dir.exists() && !dir.mkdirs()) throw new IOException("Falha ao preparar pasta");

        File out = uniqueFile(dir,name);
        try (InputStream in = getContentResolver().openInputStream(uri);
             OutputStream os = new FileOutputStream(out)) {
            if (in == null) throw new IOException("Arquivo indisponível");
            byte[] buf = new byte[262144];
            int r;
            while ((r=in.read(buf)) > 0) os.write(buf,0,r);
            os.flush();
        }
        return out;
    }

    String displayName(Uri uri) {
        try {
            if ("file".equalsIgnoreCase(uri.getScheme())) return new File(uri.getPath()).getName();
            try (Cursor c = getContentResolver().query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)) {
                if (c != null && c.moveToFirst()) {
                    int i=c.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                    if (i>=0) return c.getString(i);
                }
            }
        } catch (Throwable ignored) {}
        String last=uri.getLastPathSegment();
        return last==null?"arquivo_recebido":last;
    }

    File uniqueFile(File dir,String name) {
        File f=new File(dir,name);
        if (!f.exists()) return f;
        String base=name,ext="";
        int dot=name.lastIndexOf('.');
        if (dot>0) { base=name.substring(0,dot); ext=name.substring(dot); }
        for (int i=2;;i++) {
            f=new File(dir,base+" ("+i+")"+ext);
            if (!f.exists()) return f;
        }
    }

    int dp(int v){ return Math.round(v*getResources().getDisplayMetrics().density); }
}
