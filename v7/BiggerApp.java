package com.grupobigger.biggerotg;

import android.app.Application;
import android.content.Context;
import android.os.Build;
import android.util.Log;
import java.io.*;
import java.text.SimpleDateFormat;
import java.util.*;

public class BiggerApp extends Application {
    public static final String TAG_CRASH="CRASH";
    private static Thread.UncaughtExceptionHandler previous;

    @Override public void onCreate() {
        super.onCreate();
        previous=Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread,error)->{
            try { writeCrash(this,thread,error); }
            catch(Throwable ignored) { Log.e(TAG_CRASH,"Falha ao salvar diagnóstico",ignored); }
            if(previous!=null) previous.uncaughtException(thread,error);
        });
        pruneOldLogs(this);
    }

    public static void logNonFatal(Context c,String tag,String action,Throwable e){
        Log.e(tag,action,e);
        try{
            File dir=new File(c.getFilesDir(),"diagnostics");
            if(!dir.exists()) dir.mkdirs();
            File f=new File(dir,"nonfatal.log");
            if(f.length()>512*1024) f.delete();
            try(PrintWriter w=new PrintWriter(new FileOutputStream(f,true))){
                w.println(now()+" ["+tag+"] "+action+" -> "+e.getClass().getSimpleName()+": "+safe(e.getMessage()));
            }
        }catch(Throwable ignored){ Log.e(TAG_CRASH,"Falha no log não fatal",ignored); }
    }

    public static void markAction(Context c,String action){
        try { c.getSharedPreferences("bigger_diag",MODE_PRIVATE).edit().putString("last_action",action).apply(); }
        catch(Throwable e){ Log.e(TAG_CRASH,"Falha ao registrar ação",e); }
    }

    static void writeCrash(Context c,Thread t,Throwable e)throws Exception{
        File dir=new File(c.getFilesDir(),"diagnostics");
        if(!dir.exists()&&!dir.mkdirs()) return;
        File f=new File(dir,"crash-"+System.currentTimeMillis()+".log");
        String action="";
        try{ action=c.getSharedPreferences("bigger_diag",MODE_PRIVATE).getString("last_action",""); }catch(Throwable ignored){}
        try(PrintWriter w=new PrintWriter(new BufferedWriter(new FileWriter(f)))){
            w.println("Data: "+now());
            w.println("Android: "+Build.VERSION.RELEASE+" (SDK "+Build.VERSION.SDK_INT+")");
            w.println("Modelo: "+Build.MANUFACTURER+" "+Build.MODEL);
            w.println("Thread: "+(t==null?"?":t.getName()));
            w.println("Ultima acao: "+action);
            w.println("Excecao: "+e.getClass().getName()+": "+safe(e.getMessage()));
            e.printStackTrace(w);
        }
        pruneOldLogs(c);
    }

    static void pruneOldLogs(Context c){
        try{
            File dir=new File(c.getFilesDir(),"diagnostics");
            File[] fs=dir.listFiles((d,n)->n.startsWith("crash-")&&n.endsWith(".log"));
            if(fs==null||fs.length<=8)return;
            Arrays.sort(fs,Comparator.comparingLong(File::lastModified).reversed());
            for(int i=8;i<fs.length;i++) try{fs[i].delete();}catch(Throwable ignored){}
        }catch(Throwable e){Log.e(TAG_CRASH,"Falha ao limpar logs",e);}
    }

    static String now(){return new SimpleDateFormat("yyyy-MM-dd HH:mm:ss",Locale.US).format(new Date());}
    static String safe(String s){return s==null?"":s.replace('\n',' ').replace('\r',' ');}
}
