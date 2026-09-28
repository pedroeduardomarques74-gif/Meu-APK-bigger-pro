package com.grupobigger.biggerotg;

import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.*;
import android.provider.DocumentsContract;
import android.text.*;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;

public class AppsActivity extends Activity {
    static final int BG=Color.rgb(8,17,31), PANEL=Color.rgb(15,29,45), PANEL2=Color.rgb(19,38,58);
    static final int BLUE=Color.rgb(46,168,255), GREEN=Color.rgb(46,213,154), SOFT=Color.rgb(156,176,198), ORANGE=Color.rgb(255,174,66);

    final ArrayList<AppItem> all=new ArrayList<>(), shown=new ArrayList<>();
    final LinkedHashMap<String,AppItem> selected=new LinkedHashMap<>();
    final ExecutorService io=Executors.newSingleThreadExecutor();
    ListView list; EditText search; TextView status, selectedLabel; AppAdapter adapter;
    boolean showSystem=false; volatile boolean loading=false;

    @Override public void onCreate(Bundle b){super.onCreate(b); build(); loadAppsAsync();}
    @Override protected void onDestroy(){io.shutdownNow(); super.onDestroy();}

    void build(){
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(12),dp(10),dp(12),dp(8)); root.setBackgroundColor(BG); setContentView(root);

        LinearLayout top=row(); Button back=mini("←"); back.setOnClickListener(v->finish()); top.addView(back,new LinearLayout.LayoutParams(dp(52),dp(48)));
        LinearLayout titles=new LinearLayout(this); titles.setOrientation(LinearLayout.VERTICAL); titles.setPadding(dp(8),0,0,0);
        titles.addView(txt("APPS INSTALADOS",24,Color.WHITE,true));
        status=txt("Carregando aplicativos...",12,SOFT,false); titles.addView(status);
        top.addView(titles,new LinearLayout.LayoutParams(0,-2,1)); root.addView(top);

        search=new EditText(this); search.setHint("Pesquisar aplicativo ou pacote..."); search.setSingleLine(true); search.setTextColor(Color.WHITE); search.setHintTextColor(SOFT); search.setBackground(round(PANEL2,14)); search.setPadding(dp(14),0,dp(14),0);
        LinearLayout.LayoutParams ep=new LinearLayout.LayoutParams(-1,dp(52)); ep.setMargins(0,dp(10),0,dp(8)); root.addView(search,ep);

        LinearLayout bar=row();
        Button filter=button("👤 APPS DO USUÁRIO",PANEL2); Button refresh=button("↻ ATUALIZAR",PANEL2);
        selectedLabel=txt("0 selecionados",12,SOFT,true); selectedLabel.setGravity(Gravity.CENTER);
        bar.addView(filter,weight46()); bar.addView(refresh,weight46()); bar.addView(selectedLabel,weight46()); root.addView(bar);

        list=new ListView(this); list.setDividerHeight(dp(6)); list.setBackgroundColor(BG); adapter=new AppAdapter(); list.setAdapter(adapter); root.addView(list,new LinearLayout.LayoutParams(-1,0,1));

        LinearLayout bottom=row(); Button ex=button("EXTRAIR SELECIONADOS",BLUE); Button usb=button("EXTRAIR + USB",GREEN);
        ex.setOnClickListener(v->extractMany(new ArrayList<>(selected.values()),false,true)); usb.setOnClickListener(v->extractMany(new ArrayList<>(selected.values()),true,true));
        bottom.addView(ex,weight48()); bottom.addView(usb,weight48()); root.addView(bottom);

        search.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int a,int c,int d){} public void onTextChanged(CharSequence s,int a,int b,int c){filterList();} public void afterTextChanged(Editable e){}});
        filter.setOnClickListener(v->{showSystem=!showSystem; filter.setText(showSystem?"📱 TODOS OS APPS":"👤 APPS DO USUÁRIO"); filterList();});
        refresh.setOnClickListener(v->loadAppsAsync());
    }

    void loadAppsAsync(){
        if(loading)return; loading=true; status.setText("Carregando aplicativos...");
        io.execute(()->{
            ArrayList<AppItem> temp=new ArrayList<>(); PackageManager pm=getPackageManager();
            for(ApplicationInfo ai:pm.getInstalledApplications(PackageManager.GET_META_DATA)){
                try{
                    AppItem x=new AppItem(); x.pkg=ai.packageName; x.name=pm.getApplicationLabel(ai).toString(); x.system=(ai.flags&ApplicationInfo.FLAG_SYSTEM)!=0;
                    PackageInfo pi=pm.getPackageInfo(ai.packageName,0); x.version=pi.versionName==null?"—":pi.versionName; x.base=ai.sourceDir; x.splits=ai.splitSourceDirs==null?new String[0]:ai.splitSourceDirs;
                    x.size=size(x.base); for(String s:x.splits)x.size+=size(s); temp.add(x);
                }catch(Exception ignored){}
            }
            Collections.sort(temp,(a,b)->a.name.compareToIgnoreCase(b.name));
            runOnUiThread(()->{all.clear(); all.addAll(temp); loading=false; status.setText(all.size()+" aplicativos encontrados"); filterList();});
        });
    }

    void filterList(){
        String q=search.getText().toString().trim().toLowerCase(Locale.ROOT); shown.clear();
        for(AppItem a:all){
            if(!showSystem&&a.system)continue;
            if(!q.isEmpty()&&!a.name.toLowerCase(Locale.ROOT).contains(q)&&!a.pkg.toLowerCase(Locale.ROOT).contains(q))continue;
            shown.add(a);
        }
        adapter.notifyDataSetChanged(); status.setText(shown.size()+" exibidos • "+all.size()+" encontrados");
    }

    class AppAdapter extends BaseAdapter {
        public int getCount(){return shown.size();}
        public Object getItem(int p){return shown.get(p);}
        public long getItemId(int p){return p;}
        public View getView(int pos,View convert,android.view.ViewGroup parent){
            Holder h;
            if(convert==null){
                LinearLayout c=row(); c.setPadding(dp(8),dp(8),dp(5),dp(8)); c.setBackground(round(PANEL,16));
                CheckBox cb=new CheckBox(AppsActivity.this); ImageView iv=new ImageView(AppsActivity.this);
                LinearLayout mid=new LinearLayout(AppsActivity.this); mid.setOrientation(LinearLayout.VERTICAL); mid.setPadding(dp(10),0,dp(5),0);
                TextView n=txt("",15,Color.WHITE,true), p=txt("",10,SOFT,false), d=txt("",10,SOFT,false); mid.addView(n);mid.addView(p);mid.addView(d);
                Button more=mini("⋮"); c.addView(cb);c.addView(iv,new LinearLayout.LayoutParams(dp(46),dp(46)));c.addView(mid,new LinearLayout.LayoutParams(0,-2,1));c.addView(more,new LinearLayout.LayoutParams(dp(54),dp(48)));
                h=new Holder();h.cb=cb;h.icon=iv;h.name=n;h.pkg=p;h.desc=d;h.more=more;c.setTag(h);convert=c;
            } else h=(Holder)convert.getTag();
            AppItem a=shown.get(pos);
            h.cb.setOnCheckedChangeListener(null); h.cb.setChecked(selected.containsKey(a.pkg)); h.cb.setOnCheckedChangeListener((b,on)->{if(on)selected.put(a.pkg,a);else selected.remove(a.pkg);selectedLabel.setText(selected.size()+" selecionados");});
            h.name.setText(a.name);h.pkg.setText(a.pkg);h.desc.setText("v"+a.version+" • "+format(a.size)+" • "+(a.splits.length==0?"APK simples":"Split APK • "+(a.splits.length+1))+(a.system?" • Sistema":""));
            h.desc.setTextColor(a.splits.length==0?GREEN:ORANGE);
            try{h.icon.setImageDrawable(getPackageManager().getApplicationIcon(a.pkg));}catch(Exception e){h.icon.setImageDrawable(null);}
            h.more.setOnClickListener(v->menu(a)); return convert;
        }
    }
    static class Holder{CheckBox cb;ImageView icon;TextView name,pkg,desc;Button more;}

    void menu(AppItem a){
        ArrayList<String> o=new ArrayList<>();o.add("Extrair APK");if(a.splits.length>0)o.add("Backup completo (base + splits)");o.add("Extrair e enviar ao USB");o.add("Detalhes");
        new AlertDialog.Builder(this).setTitle(a.name).setItems(o.toArray(new String[0]),(d,w)->{String s=o.get(w);if(s.equals("Extrair APK"))extractMany(Collections.singletonList(a),false,false);else if(s.startsWith("Backup"))extractMany(Collections.singletonList(a),false,true);else if(s.startsWith("Extrair e"))extractMany(Collections.singletonList(a),true,true);else details(a);}).show();
    }
    void details(AppItem a){new AlertDialog.Builder(this).setTitle(a.name).setMessage("Pacote: "+a.pkg+"\nVersão: "+a.version+"\nTipo: "+(a.system?"Sistema":"Usuário")+"\nFormato: "+(a.splits.length==0?"APK simples":"Split APK")+"\nTamanho: "+format(a.size)+"\nArquivos APK: "+(a.splits.length+1)).setPositiveButton("OK",null).show();}

    void extractMany(List<AppItem> src,boolean toUsb,boolean full){
        if(src.isEmpty()){toast("Selecione pelo menos um aplicativo.");return;}
        Uri usb=toUsb?savedUsb():null;if(toUsb&&usb==null){toast("Abra e autorize o USB no BIGGER OTG primeiro.");return;}
        ProgressDialog pd=new ProgressDialog(this);pd.setTitle(toUsb?"Extraindo e enviando ao USB":"Extraindo APKs");pd.setProgressStyle(ProgressDialog.STYLE_HORIZONTAL);pd.setMax(src.size());pd.setCancelable(false);pd.show();
        io.execute(()->{ArrayList<String> paths=new ArrayList<>();int ok=0;
            for(int i=0;i<src.size();i++){AppItem a=src.get(i);final int n=i;runOnUiThread(()->{pd.setMessage(a.name);pd.setProgress(n);});try{List<File> out=extract(a,full);if(!out.isEmpty()){ok++;for(File f:out){paths.add(f.getAbsolutePath());if(toUsb)copyToUsb(f,usb);}}}catch(Exception ignored){}}
            int good=ok;runOnUiThread(()->{pd.dismiss();selected.clear();selectedLabel.setText("0 selecionados");adapter.notifyDataSetChanged();toast(good+" de "+src.size()+" aplicativo(s) extraído(s).");openInBigger(paths);});
        });
    }

    List<File> extract(AppItem a,boolean full)throws Exception{
        File root=new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),"BIGGER OTG/APKs Extraidos");if(!root.exists())root.mkdirs();ArrayList<File> out=new ArrayList<>();String n=safe(a.name),v=safe(a.version);
        if(a.splits.length==0||!full){File d=new File(root,n+"_"+v+".apk");copy(new File(a.base),d);out.add(d);return out;}
        File dir=new File(root,n+"_"+v+"_SPLIT");if(!dir.exists())dir.mkdirs();File b=new File(dir,n+"_base.apk");copy(new File(a.base),b);out.add(b);
        for(int i=0;i<a.splits.length;i++){File s=new File(a.splits[i]);String nm=s.getName().endsWith(".apk")?s.getName():"split_"+(i+1)+".apk";File d=new File(dir,nm);copy(s,d);out.add(d);}return out;
    }

    Uri savedUsb(){String u=getSharedPreferences("bigger_otg",MODE_PRIVATE).getString("usb",null);return u==null?null:Uri.parse(u);}
    void copyToUsb(File f,Uri tree)throws Exception{String rootId=DocumentsContract.getTreeDocumentId(tree);Uri parent=DocumentsContract.buildDocumentUriUsingTree(tree,rootId);Uri dest=DocumentsContract.createDocument(getContentResolver(),parent,"application/vnd.android.package-archive",f.getName());if(dest==null)return;try(InputStream in=new FileInputStream(f);OutputStream out=getContentResolver().openOutputStream(dest,"w")){byte[] b=new byte[262144];int r;while((r=in.read(b))>0)out.write(b,0,r);}}
    void openInBigger(ArrayList<String> paths){if(paths.isEmpty())return;Intent i=new Intent(this,MainActivity.class);i.putStringArrayListExtra("bigger_extracted_paths",paths);i.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);startActivity(i);finish();}
    void copy(File a,File b)throws Exception{try(InputStream in=new FileInputStream(a);OutputStream out=new FileOutputStream(b)){byte[] x=new byte[262144];int r;while((r=in.read(x))>0)out.write(x,0,r);}}
    long size(String p){try{return new File(p).length();}catch(Exception e){return 0;}}
    String safe(String s){return s==null?"app":s.replaceAll("[^a-zA-Z0-9._ -]","_").trim();}
    String format(long b){if(b<=0)return"0 B";String[]u={"B","KB","MB","GB"};int i=(int)(Math.log(b)/Math.log(1024));i=Math.max(0,Math.min(i,u.length-1));return String.format(Locale.US,"%.1f %s",b/Math.pow(1024,i),u[i]);}
    void toast(String s){Toast.makeText(this,s,Toast.LENGTH_SHORT).show();}
    int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
    TextView txt(String s,int z,int c,boolean bold){TextView v=new TextView(this);v.setText(s);v.setTextSize(z);v.setTextColor(c);if(bold)v.setTypeface(null,1);return v;}
    LinearLayout row(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.HORIZONTAL);l.setGravity(Gravity.CENTER_VERTICAL);return l;}
    Button button(String s,int c){Button b=new Button(this);b.setText(s);b.setTextColor(Color.WHITE);b.setTextSize(11);b.setAllCaps(false);b.setBackground(round(c,12));return b;}
    Button mini(String s){Button b=button(s,PANEL2);b.setMinWidth(0);b.setMinimumWidth(0);return b;}
    GradientDrawable round(int c,int r){GradientDrawable g=new GradientDrawable();g.setColor(c);g.setCornerRadius(dp(r));return g;}
    LinearLayout.LayoutParams weight46(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,dp(46),1);p.setMargins(dp(2),dp(2),dp(2),dp(2));return p;}
    LinearLayout.LayoutParams weight48(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,dp(50),1);p.setMargins(dp(3),dp(3),dp(3),dp(3));return p;}
    static class AppItem{String name,pkg,version,base;String[]splits;boolean system;long size;}
}