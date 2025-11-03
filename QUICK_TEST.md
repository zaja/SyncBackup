# Quick Test - Windows Service

## Brzi test (5 minuta)

Otvori **PowerShell kao Administrator** i izvršavaj naredbe redom:

### 1. Ukloni stari servis
```powershell
sc stop SyncBackupService
sc delete SyncBackupService
```

### 2. Navigiraj u folder
```powershell
cd "C:\Users\Zaja\Desktop\synhroapp – app"
```

### 3. Instaliraj servis
```powershell
python service_manager.py install
```

**Očekivani output:**
```
======================================================================
SyncBackup Service Manager
======================================================================

Installing SyncBackup Windows Service...
Service script: C:\Users\Zaja\Desktop\synhroapp – app\app\windows_service.py
Python executable: C:\...\python.exe
✓ Service 'SyncBackup - Folder Sync & Backup Service' installed successfully
  Service name: SyncBackupService
  Startup type: Automatic

You can now start the service with: python ... start
Or use Windows Services Manager (services.msc)
```

### 4. Provjeri status
```powershell
python service_manager.py status
```

**Očekivani output:**
```
Service Status: Stopped
```

### 5. Provjeri u services.msc
```powershell
services.msc
```

**Traži:** "SyncBackup - Folder Sync & Backup Service"  
**Trebao bi biti:** Vidljiv u popisu, Status: Stopped, Startup Type: Automatic

### 6. Testiraj u debug modu
```powershell
python service_manager.py debug
```

**Očekivano:**
- Servis se pokreće u konzoli
- Vidiš poruke o radu servisa
- Pritisni Ctrl+C za zaustavljanje

### 7. Pokreni kao servis
```powershell
python service_manager.py start
```

**Očekivani output:**
```
Service 'SyncBackup - Folder Sync & Backup Service' started successfully
```

### 8. Provjeri da li radi
```powershell
python service_manager.py status
```

**Očekivani output:**
```
Service Status: Running
```

### 9. Provjeri log
```powershell
type app\service.log
```

**Očekivano:**
- Vidiš log poruke o pokretanju servisa
- "Service started"
- "SyncBackup service running in background mode"

### 10. Zaustavi servis
```powershell
python service_manager.py stop
```

## Ako nešto ne radi

### Greška: "Access Denied"
```powershell
# Pokreni PowerShell kao Administrator
# Right-click PowerShell → Run as Administrator
```

### Greška: "Service already exists"
```powershell
sc delete SyncBackupService
# Pa ponovi instalaciju
```

### Greška: "ModuleNotFoundError: No module named 'app'"
```powershell
# Provjeri error log
type app\service_error.log

# Testiraj import
python -c "import sys; sys.path.insert(0, '.'); import app.database; print('OK')"
```

### Servis se ne vidi u services.msc
```powershell
# Provjeri da li je instaliran
sc query SyncBackupService

# Ako nije, reinstaliraj
python service_manager.py install
```

### Servis se ne pokreće
```powershell
# Provjeri logove
type app\service.log
type app\service_error.log

# Testiraj u debug modu
python service_manager.py debug
```

## Sve naredbe

```powershell
# Instalacija i upravljanje
python service_manager.py install
python service_manager.py start
python service_manager.py stop
python service_manager.py restart
python service_manager.py status
python service_manager.py uninstall
python service_manager.py debug

# Provjera
sc query SyncBackupService
services.msc

# Logovi
type app\service.log
type app\service_error.log
Get-Content app\service.log -Wait  # Real-time log
```

## Očekivani rezultat

✅ Servis instaliran  
✅ Vidljiv u services.msc  
✅ Pokreće se bez grešaka  
✅ Logovi se pišu u app\service.log  
✅ Status: Running  

## Pomoć

Detaljne upute:
- `SERVIS_UPUTE.md` (Hrvatski)
- `SERVICE_TROUBLESHOOTING.md` (English)
- `WINDOWS_SERVICE_FIX.md` (Quick fix)
