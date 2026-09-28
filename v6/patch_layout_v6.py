from pathlib import Path

main = Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java")
s = main.read_text()

# 1) Estado global de insets
needle = '    long lastAutoPrompt = 0L;\n'
insert = '''    long lastAutoPrompt = 0L;
    int safeBaseLeft = 0, safeBaseTop = 0, safeBaseRight = 0, safeBaseBottom = 0;
    int insetLeft = 0, insetTop = 0, insetRight = 0, insetBottom = 0;
'''
if needle not in s:
    raise SystemExit("campo lastAutoPrompt não encontrado")
s = s.replace(needle, insert, 1)

# 2) Configuração edge-to-edge + insets raiz
needle = '''        rootContainer.setOrientation(LinearLayout.VERTICAL);
        setContentView(rootContainer);
        registerUsbReceiver();'''
replacement = '''        rootContainer.setOrientation(LinearLayout.VERTICAL);
        setContentView(rootContainer);
        configureEdgeToEdge();
        installRootInsets();
        registerUsbReceiver();'''
if needle not in s:
    raise SystemExit("onCreate raiz não encontrado")
s = s.replace(needle, replacement, 1)

# 3) Métodos globais para status/nav/cutout
marker = '    void registerUsbReceiver() {'
methods = r'''    void configureEdgeToEdge() {
        Window w = getWindow();
        w.setStatusBarColor(Color.TRANSPARENT);
        w.setNavigationBarColor(Color.TRANSPARENT);
        if (Build.VERSION.SDK_INT >= 30) {
            w.setDecorFitsSystemWindows(false);
        } else {
            w.getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            );
        }
    }

    void installRootInsets() {
        rootContainer.setOnApplyWindowInsetsListener((v, insets) -> {
            int l, t, r, b;
            if (Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets bars = insets.getInsets(
                    WindowInsets.Type.systemBars() |
                    WindowInsets.Type.displayCutout() |
                    WindowInsets.Type.mandatorySystemGestures()
                );
                l = bars.left; t = bars.top; r = bars.right; b = bars.bottom;
            } else {
                l = insets.getSystemWindowInsetLeft();
                t = insets.getSystemWindowInsetTop();
                r = insets.getSystemWindowInsetRight();
                b = insets.getSystemWindowInsetBottom();
                if (Build.VERSION.SDK_INT >= 28 && insets.getDisplayCutout() != null) {
                    android.view.DisplayCutout c = insets.getDisplayCutout();
                    l = Math.max(l, c.getSafeInsetLeft());
                    t = Math.max(t, c.getSafeInsetTop());
                    r = Math.max(r, c.getSafeInsetRight());
                    b = Math.max(b, c.getSafeInsetBottom());
                }
            }
            insetLeft=l; insetTop=t; insetRight=r; insetBottom=b;
            applyRootInsetsNow();
            return insets;
        });
        rootContainer.post(() -> rootContainer.requestApplyInsets());
    }

    void setRootBasePaddingDp(int l, int t, int r, int b) {
        safeBaseLeft=dp(l); safeBaseTop=dp(t); safeBaseRight=dp(r); safeBaseBottom=dp(b);
        applyRootInsetsNow();
        rootContainer.requestApplyInsets();
    }

    void applyRootInsetsNow() {
        if (rootContainer == null) return;
        rootContainer.setPadding(
            safeBaseLeft + insetLeft,
            safeBaseTop + insetTop,
            safeBaseRight + insetRight,
            safeBaseBottom + insetBottom
        );
    }

'''
if marker not in s:
    raise SystemExit("marker registerUsbReceiver não encontrado")
s = s.replace(marker, methods + marker, 1)

# 4) Padding raiz das telas respeitando insets
s = s.replace('        rootContainer.setPadding(dp(16),dp(18),dp(16),dp(18));',
              '        setRootBasePaddingDp(16,18,16,18);')
s = s.replace('        rootContainer.setPadding(dp(12),dp(8),dp(12),dp(8));',
              '        setRootBasePaddingDp(12,8,12,8);')

needle = '''    void showMainUi() {
        wizardVisible = false;
        rootContainer.removeAllViews();'''
replacement = '''    void showMainUi() {
        wizardVisible = false;
        rootContainer.removeAllViews();
        setRootBasePaddingDp(0,0,0,0);'''
if needle not in s:
    raise SystemExit("showMainUi não encontrado")
s = s.replace(needle, replacement, 1)

# 5) Scroll da tela principal
s = s.replace('        ScrollView scroll = new ScrollView(this); LinearLayout content = new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL);',
              '        ScrollView scroll = new ScrollView(this); scroll.setFillViewport(true); scroll.setClipToPadding(false); LinearLayout content = new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL);')

# 6) Campos e botões sem altura rígida
s = s.replace('        rootContainer.addView(continueBtn,new LinearLayout.LayoutParams(-1,dp(56)));',
              '        continueBtn.setMinHeight(dp(56)); rootContainer.addView(continueBtn,new LinearLayout.LayoutParams(-1,-2));')

s = s.replace('view.addView(search,new LinearLayout.LayoutParams(-1,dp(48)));',
              'search.setMinHeight(dp(48)); view.addView(search,new LinearLayout.LayoutParams(-1,-2));')

# Legacy installed-apps screen still present in MainActivity: make it adaptive too
s = s.replace('LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(-1,dp(52));',
              'search.setMinHeight(dp(52)); LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(-1,-2);')
s = s.replace('tools.addView(filter,new LinearLayout.LayoutParams(0,dp(46),1)); tools.addView(refresh,new LinearLayout.LayoutParams(0,dp(46),1)); tools.addView(selectedLabel,new LinearLayout.LayoutParams(0,dp(46),1));',
              'filter.setMinHeight(dp(46)); refresh.setMinHeight(dp(46)); selectedLabel.setMinHeight(dp(46)); tools.addView(filter,new LinearLayout.LayoutParams(0,-2,1)); tools.addView(refresh,new LinearLayout.LayoutParams(0,-2,1)); tools.addView(selectedLabel,new LinearLayout.LayoutParams(0,-2,1));')
s = s.replace('ScrollView sv=new ScrollView(this); sv.addView(list);',
              'ScrollView sv=new ScrollView(this); sv.setFillViewport(true); sv.setClipToPadding(false); sv.addView(list);')

# 7) Pane header: título em linha própria + controles abaixo para não esmagar em telas pequenas/fonte grande
old = '''            LinearLayout head=horizontal(); TextView t=txt(name,18,Color.WHITE,true); head.addView(t,weight());
            Button up=mini("↑"); up.setOnClickListener(v->up()); head.addView(up);
            Button folder=mini("＋ Pasta"); folder.setOnClickListener(v->newFolder()); head.addView(folder);
            Button pick=mini(isUsb ? "Abrir USB" : "Abrir"); pick.setOnClickListener(v->{ if(isUsb) autoConnectUsb(true); else choose(false); }); head.addView(pick); view.addView(head);'''
new = '''            LinearLayout titleRow=horizontal(); TextView t=txt(name,18,Color.WHITE,true); titleRow.addView(t,new LinearLayout.LayoutParams(-1,-2)); view.addView(titleRow);
            LinearLayout head=horizontal();
            Button up=mini("↑"); up.setOnClickListener(v->up()); head.addView(up,weight());
            Button folder=mini("＋ Pasta"); folder.setOnClickListener(v->newFolder()); head.addView(folder,weight());
            Button pick=mini(isUsb ? "Abrir USB" : "Abrir"); pick.setOnClickListener(v->{ if(isUsb) autoConnectUsb(true); else choose(false); }); head.addView(pick,weight()); view.addView(head);'''
if old not in s:
    raise SystemExit("cabeçalho Pane não encontrado")
s = s.replace(old, new, 1)

# 8) Helpers globais: texto/botão responsivos e sem altura fixa
old = '''    Button button(String s,int color){Button b=new Button(this);b.setText(s);b.setTextColor(Color.WHITE);b.setTextSize(12);b.setAllCaps(false);b.setBackground(round(color,12));b.setPadding(dp(4),0,dp(4),0);return b;}
    Button mini(String s){Button b=button(s,PANEL2);b.setMinWidth(0);b.setMinimumWidth(0);b.setPadding(dp(8),0,dp(8),0);return b;}
    GradientDrawable round(int color,int radius){GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(dp(radius));return g;}
    LinearLayout.LayoutParams weight(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,dp(48),1);p.setMargins(dp(3),dp(3),dp(3),dp(3));return p;}'''
new = '''    Button button(String s,int color){Button b=new Button(this);b.setText(s);b.setTextColor(Color.WHITE);b.setTextSize(12);b.setAllCaps(false);b.setGravity(Gravity.CENTER);b.setMinHeight(dp(48));b.setMinimumHeight(dp(48));b.setSingleLine(false);b.setMaxLines(3);b.setBackground(round(color,12));b.setPadding(dp(8),dp(8),dp(8),dp(8));return b;}
    Button mini(String s){Button b=button(s,PANEL2);b.setMinWidth(0);b.setMinimumWidth(0);b.setPadding(dp(8),dp(6),dp(8),dp(6));return b;}
    GradientDrawable round(int color,int radius){GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(dp(radius));return g;}
    LinearLayout.LayoutParams weight(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,-2,1);p.setMargins(dp(3),dp(3),dp(3),dp(3));return p;}'''
if old not in s:
    raise SystemExit("helpers button/weight não encontrados")
s = s.replace(old, new, 1)

main.write_text(s)

# AppsActivity: insets + layout adaptativo
apps = Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/AppsActivity.java")
a = apps.read_text()

needle = '    boolean showSystem=false; volatile boolean loading=false;\n'
insert = '''    boolean showSystem=false; volatile boolean loading=false;
    int baseLeft,baseTop,baseRight,baseBottom;
'''
if needle not in a:
    raise SystemExit("AppsActivity campos não encontrados")
a = a.replace(needle, insert, 1)

a = a.replace('@Override public void onCreate(Bundle b){super.onCreate(b); build(); loadAppsAsync();}',
'''@Override public void onCreate(Bundle b){
        super.onCreate(b);
        configureEdgeToEdge();
        build();
        loadAppsAsync();
    }''')

# root padding vai ser aplicado pelos insets
old = 'LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(dp(12),dp(10),dp(12),dp(8)); root.setBackgroundColor(BG); setContentView(root);'
new = 'LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(BG); setContentView(root); installInsets(root,12,10,12,8);'
if old not in a:
    raise SystemExit("AppsActivity root não encontrado")
a = a.replace(old, new, 1)

# Cabeçalho e campos sem altura rígida
a = a.replace('top.addView(back,new LinearLayout.LayoutParams(dp(52),dp(48)));',
              'back.setMinWidth(dp(52)); back.setMinHeight(dp(48)); top.addView(back,new LinearLayout.LayoutParams(-2,-2));')
a = a.replace('LinearLayout.LayoutParams ep=new LinearLayout.LayoutParams(-1,dp(52));',
              'search.setMinHeight(dp(52)); LinearLayout.LayoutParams ep=new LinearLayout.LayoutParams(-1,-2);')
a = a.replace('list=new ListView(this); list.setDividerHeight(dp(6)); list.setBackgroundColor(BG);',
              'list=new ListView(this); list.setDividerHeight(dp(6)); list.setBackgroundColor(BG); list.setClipToPadding(false);')

# Botões/lista rows
a = a.replace('c.addView(more,new LinearLayout.LayoutParams(dp(54),dp(48)));',
              'more.setMinWidth(dp(54)); more.setMinHeight(dp(48)); c.addView(more,new LinearLayout.LayoutParams(-2,-2));')

old = '''    void loadAppsAsync(){'''
methods = r'''    void configureEdgeToEdge(){
        Window w=getWindow();
        w.setStatusBarColor(Color.TRANSPARENT);
        w.setNavigationBarColor(Color.TRANSPARENT);
        if(Build.VERSION.SDK_INT>=30){
            w.setDecorFitsSystemWindows(false);
        }else{
            w.getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            );
        }
    }

    void installInsets(View root,int lDp,int tDp,int rDp,int bDp){
        baseLeft=dp(lDp);baseTop=dp(tDp);baseRight=dp(rDp);baseBottom=dp(bDp);
        root.setOnApplyWindowInsetsListener((v,insets)->{
            int l,t,r,b;
            if(Build.VERSION.SDK_INT>=30){
                android.graphics.Insets bars=insets.getInsets(
                    WindowInsets.Type.systemBars() |
                    WindowInsets.Type.displayCutout() |
                    WindowInsets.Type.mandatorySystemGestures()
                );
                l=bars.left;t=bars.top;r=bars.right;b=bars.bottom;
            }else{
                l=insets.getSystemWindowInsetLeft();
                t=insets.getSystemWindowInsetTop();
                r=insets.getSystemWindowInsetRight();
                b=insets.getSystemWindowInsetBottom();
                if(Build.VERSION.SDK_INT>=28 && insets.getDisplayCutout()!=null){
                    android.view.DisplayCutout c=insets.getDisplayCutout();
                    l=Math.max(l,c.getSafeInsetLeft());t=Math.max(t,c.getSafeInsetTop());
                    r=Math.max(r,c.getSafeInsetRight());b=Math.max(b,c.getSafeInsetBottom());
                }
            }
            v.setPadding(baseLeft+l,baseTop+t,baseRight+r,baseBottom+b);
            return insets;
        });
        root.post(root::requestApplyInsets);
    }

'''
if old not in a:
    raise SystemExit("AppsActivity loadAppsAsync marker não encontrado")
a = a.replace(old, methods + old, 1)

# Helpers do AppsActivity com wrap_content + minHeight
old = '''    Button button(String s,int c){Button b=new Button(this);b.setText(s);b.setTextColor(Color.WHITE);b.setTextSize(11);b.setAllCaps(false);b.setBackground(round(c,12));return b;}
    Button mini(String s){Button b=button(s,PANEL2);b.setMinWidth(0);b.setMinimumWidth(0);return b;}
    GradientDrawable round(int c,int r){GradientDrawable g=new GradientDrawable();g.setColor(c);g.setCornerRadius(dp(r));return g;}
    LinearLayout.LayoutParams weight46(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,dp(46),1);p.setMargins(dp(2),dp(2),dp(2),dp(2));return p;}
    LinearLayout.LayoutParams weight48(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,dp(50),1);p.setMargins(dp(3),dp(3),dp(3),dp(3));return p;}'''
new = '''    Button button(String s,int c){Button b=new Button(this);b.setText(s);b.setTextColor(Color.WHITE);b.setTextSize(11);b.setAllCaps(false);b.setGravity(Gravity.CENTER);b.setMinHeight(dp(48));b.setMinimumHeight(dp(48));b.setSingleLine(false);b.setMaxLines(3);b.setPadding(dp(8),dp(7),dp(8),dp(7));b.setBackground(round(c,12));return b;}
    Button mini(String s){Button b=button(s,PANEL2);b.setMinWidth(0);b.setMinimumWidth(0);return b;}
    GradientDrawable round(int c,int r){GradientDrawable g=new GradientDrawable();g.setColor(c);g.setCornerRadius(dp(r));return g;}
    LinearLayout.LayoutParams weight46(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,-2,1);p.setMargins(dp(2),dp(2),dp(2),dp(2));return p;}
    LinearLayout.LayoutParams weight48(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,-2,1);p.setMargins(dp(3),dp(3),dp(3),dp(3));return p;}'''
if old not in a:
    raise SystemExit("AppsActivity helpers não encontrados")
a = a.replace(old, new, 1)

apps.write_text(a)

# Tema: barras transparentes apenas porque agora todas as telas tratam WindowInsets
styles = Path("buildsrc/app/src/main/res/values/styles.xml")
st = styles.read_text()
st = st.replace('<item name="android:statusBarColor">#08111F</item>', '<item name="android:statusBarColor">@android:color/transparent</item>')
st = st.replace('<item name="android:navigationBarColor">#08111F</item>', '<item name="android:navigationBarColor">@android:color/transparent</item>')
styles.write_text(st)

# Versão
gradle = Path("buildsrc/app/build.gradle")
g = gradle.read_text().replace('versionCode 7','versionCode 8').replace("versionName '5.2.0'","versionName '6.0.0'")
gradle.write_text(g)
