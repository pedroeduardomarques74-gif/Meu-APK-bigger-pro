package com.grupobigger.biggerotg;

import android.content.*;
import android.content.pm.ProviderInfo;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.*;

public class ShareFileProvider extends ContentProvider {
    File cacheRoot;

    @Override public void attachInfo(Context context, ProviderInfo info){
        super.attachInfo(context,info);
        cacheRoot=context.getCacheDir();
    }

    static Uri uriFor(Context c,File f)throws IOException{
        File root=c.getCacheDir().getCanonicalFile();
        File file=f.getCanonicalFile();
        String rp=root.getPath()+File.separator;
        if(!file.getPath().startsWith(rp))throw new SecurityException("Arquivo fora do cache permitido");
        String rel=file.getPath().substring(rp.length());
        return new Uri.Builder()
            .scheme("content")
            .authority(c.getPackageName()+".sharefiles")
            .appendPath("cache")
            .appendPath(rel)
            .build();
    }

    File resolve(Uri uri)throws IOException{
        if(uri==null||uri.getPathSegments().size()<2)throw new FileNotFoundException("URI inválida");
        if(!"cache".equals(uri.getPathSegments().get(0)))throw new FileNotFoundException("Origem inválida");
        String rel=uri.getPathSegments().get(1);
        File root=cacheRoot.getCanonicalFile();
        File f=new File(root,rel).getCanonicalFile();
        String rp=root.getPath()+File.separator;
        if(!f.getPath().startsWith(rp)||!f.exists()||!f.isFile())throw new FileNotFoundException("Arquivo indisponível");
        return f;
    }

    @Override public String getType(Uri uri){
        try{
            String n=resolve(uri).getName().toLowerCase(java.util.Locale.ROOT);
            if(n.endsWith(".apk"))return "application/vnd.android.package-archive";
            if(n.endsWith(".zip"))return "application/zip";
        }catch(Throwable ignored){}
        return "application/octet-stream";
    }

    @Override public Cursor query(Uri uri,String[] projection,String selection,String[] selectionArgs,String sortOrder){
        try{
            File f=resolve(uri);
            MatrixCursor c=new MatrixCursor(new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE});
            c.addRow(new Object[]{f.getName(),f.length()});
            return c;
        }catch(Throwable e){
            return new MatrixCursor(new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE});
        }
    }

    @Override public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException{
        if(mode==null||!mode.startsWith("r"))throw new FileNotFoundException("Somente leitura");
        try{return ParcelFileDescriptor.open(resolve(uri),ParcelFileDescriptor.MODE_READ_ONLY);}
        catch(IOException e){throw new FileNotFoundException(e.getMessage());}
    }

    @Override public Uri insert(Uri uri,ContentValues values){throw new UnsupportedOperationException("Somente leitura");}
    @Override public int delete(Uri uri,String selection,String[] selectionArgs){return 0;}
    @Override public int update(Uri uri,ContentValues values,String selection,String[] selectionArgs){return 0;}
    @Override public boolean onCreate(){return true;}
}
