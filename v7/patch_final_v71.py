from pathlib import Path

p=Path("buildsrc/app/src/main/java/com/grupobigger/biggerotg/MainActivity.java")
s=p.read_text()

s=s.replace('''            } catch (Throwable ignored) {
                return null;
            }
        } catch (Throwable ignored) {
            return null;
        }
    }''','''            } catch (Throwable e) {
                BiggerApp.logNonFatal(this,"APK_ICON","Falha ao carregar ícone do APK",e);
                return null;
            }
        } catch (Throwable e) {
            BiggerApp.logNonFatal(this,"APK_ICON","Falha ao analisar APK externo",e);
            return null;
        }
    }''',1)

s=s.replace('''        } catch (Throwable ignored) {
            toast("Arquivo recebido. Abra a pasta do celular para localizar.");
        }''','''        } catch (Throwable e) {
            BiggerApp.logNonFatal(this,"SHARE_INTENT","Falha ao mostrar arquivo recebido",e);
            toast("Arquivo recebido. Abra a pasta do celular para localizar.");
        }''',1)

s=s.replace('''        try { takePersistablePermissionChecked(uri, flags); } catch(Exception ignored) {
            try { getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION); } catch(Exception ignored2){ BiggerApp.logNonFatal(MainActivity.this,"RECOVERY","Exceção recuperada", ignored2); }
        }''','''        try { takePersistablePermissionChecked(uri, flags); } catch(Exception e) {
            BiggerApp.logNonFatal(this,"PERMISSION","Falha na permissão persistente inicial",e);
            try { getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION); }
            catch(Exception e2){ BiggerApp.logNonFatal(this,"PERMISSION","Falha na permissão persistente alternativa",e2); }
        }''',1)

s=s.replace('''                io.execute(()->{ try{ Uri parent=docUri(treeUri,currentDocId); DocumentsContract.createDocument(getContentResolver(),parent,DocumentsContract.Document.MIME_TYPE_DIR,name); runOnUiThread(()->{toast("Pasta criada.");load();}); }catch(Exception ex){runOnUiThread(()->toast("Não foi possível criar a pasta."));} });''','''                io.execute(()->{ try{
                    Uri parent=docUri(treeUri,currentDocId);
                    Uri made=DocumentsContract.createDocument(getContentResolver(),parent,DocumentsContract.Document.MIME_TYPE_DIR,safeFileName(name));
                    if(made==null)throw new java.io.IOException("Provider não criou a pasta");
                    safeUi(()->{toast("Pasta criada.");load();});
                }catch(Throwable ex){
                    BiggerApp.logNonFatal(MainActivity.this,isUsb?"USB_OTG":"FILE_MANAGER","Criar pasta",ex);
                    safeUi(()->toast(isUsb?"Não foi possível criar a pasta no USB.":"Não foi possível criar a pasta."));
                } });''',1)

s=s.replace('''                try{ DocumentsContract.renameDocument(getContentResolver(),docUri(treeUri,n.id),e.getText().toString().trim()); runOnUiThread(()->{toast("Renomeado.");load();}); }catch(Exception ex){runOnUiThread(()->toast("Falha ao renomear."));}''','''                try{
                    String newName=safeFileName(e.getText().toString().trim());
                    if(newName.isEmpty())throw new IllegalArgumentException("Nome vazio");
                    Uri renamed=DocumentsContract.renameDocument(getContentResolver(),docUri(treeUri,n.id),newName);
                    if(renamed==null)throw new java.io.IOException("Provider não renomeou");
                    safeUi(()->{toast("Renomeado.");load();});
                }catch(Throwable ex){
                    BiggerApp.logNonFatal(MainActivity.this,isUsb?"USB_OTG":"FILE_MANAGER","Renomear arquivo",ex);
                    safeUi(()->toast("Falha ao renomear."));
                }''',1)

s=s.replace('''            try{ DocumentsContract.deleteDocument(getContentResolver(),docUri(treeUri,n.id)); runOnUiThread(()->{selected.remove(n.id);toast("Excluído.");load();}); }catch(Exception ex){runOnUiThread(()->toast("Falha ao excluir."));}''','''            try{
                boolean ok=DocumentsContract.deleteDocument(getContentResolver(),docUri(treeUri,n.id));
                if(!ok)throw new java.io.IOException("Provider recusou exclusão");
                safeUi(()->{selected.remove(n.id);toast("Excluído.");load();});
            }catch(Throwable ex){
                BiggerApp.logNonFatal(MainActivity.this,isUsb?"USB_OTG":"FILE_MANAGER","Excluir arquivo",ex);
                safeUi(()->toast("Falha ao excluir."));
            }''',1)

p.write_text(s)

# v7.1
b=Path("buildsrc/app/build.gradle")
g=b.read_text().replace('versionCode 15','versionCode 16').replace("versionName '7.0.0'","versionName '7.1.0'")
b.write_text(g)
