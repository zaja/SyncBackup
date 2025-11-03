# Windows Service - Brzi Fix (Quick Fix)

## Problem

```
Error 0xC0000004 - Python could not import the service's module
ModuleNotFoundError: No module named 'app'
```

Servis se nije vidio u `services.msc` iako je instalacija prijavila uspjeh.

## Što je popravljeno

### 1. Python putanje (sys.path)
**Problem**: Windows servis pokreće Python u drugačijem kontekstu gdje `app` modul nije bio dostupan.

**Rješenje**: Dodao sam eksplicitno postavljanje `sys.path` na **samom početku** `windows_service.py` prije svih importa:

```python
# CRITICAL: Add parent directory to path BEFORE any other imports
_service_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_service_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)
```

### 2. Registracija servisa
**Problem**: Korištenje `HandleCommandLine` nije bilo dovoljno pouzdano.

**Rješenje**: Sada koristim `InstallService` direktno s eksplicitnim parametrima:

```python
win32serviceutil.InstallService(
    ServiceClass._svc_reg_class_,
    ServiceClass._svc_name_,
    ServiceClass._svc_display_name_,
    description=ServiceClass._svc_description_,
    exeName=sys.executable,
    exeArgs=f'"{service_script}"'
)
```

### 3. Nedostajući atributi
**Problem**: Servisu su nedostajali potrebni atributi za Windows Service Manager.

**Rješenje**: Dodao sam:
```python
_svc_reg_class_ = "PythonService"
_exe_name_ = sys.executable
_exe_args_ = f'"{os.path.abspath(__file__)}"'
```

### 4. Bolji error handling
**Problem**: Greške pri pokretanju nisu bile logirane.

**Rješenje**: Dodao sam logging u `service_error.log` za lakše debugiranje.

## Kako testirati

### Brzi test (5 minuta)

1. **Ukloni stari servis** (ako postoji):
```powershell
sc stop SyncBackupService
sc delete SyncBackupService
```

2. **Instaliraj novi servis** (kao Administrator):
```powershell
cd "C:\Users\Zaja\Desktop\synhroapp – app"
python service_manager.py install
```

3. **Provjeri je li vidljiv**:
```powershell
python service_manager.py status
# ili
services.msc
```

4. **Testiraj u debug modu**:
```powershell
python service_manager.py debug
```
Pritisni Ctrl+C za zaustavljanje.

5. **Pokreni kao servis**:
```powershell
python service_manager.py start
python service_manager.py status
```

## Novi alati

### service_manager.py
Novi helper script za lakše upravljanje servisom:

```powershell
python service_manager.py install    # Instaliraj
python service_manager.py start      # Pokreni
python service_manager.py stop       # Zaustavi
python service_manager.py status     # Status
python service_manager.py uninstall  # Ukloni
python service_manager.py debug      # Debug mod
```

### Dokumentacija
- `SERVIS_UPUTE.md` - Kratke upute (Hrvatski)
- `SERVICE_TROUBLESHOOTING.md` - Detaljan troubleshooting (English)

## Očekivani rezultat

Nakon instalacije, servis bi trebao biti:
- ✅ Vidljiv u `services.msc` kao "SyncBackup - Folder Sync & Backup Service"
- ✅ Pokretljiv bez grešaka
- ✅ Sposoban izvršavati job-ove u pozadini
- ✅ Auto-start postavljen na "Automatic"

## Ako i dalje ne radi

1. Provjeri logove:
```powershell
type app\service.log
type app\service_error.log
```

2. Pokreni u debug modu:
```powershell
python service_manager.py debug
```

3. Provjeri Windows Event Log:
```powershell
eventvwr.msc
# Navigate to: Windows Logs > Application
# Traži: SyncBackupService
```

4. Provjeri da li je pywin32 instaliran:
```powershell
pip show pywin32
```

## Izmijenjeni fajlovi

- ✅ `app/windows_service.py` - Popravljene putanje i registracija
- ✅ `service_manager.py` - Novi helper script (NOVO)
- ✅ `SERVIS_UPUTE.md` - Upute na hrvatskom (NOVO)
- ✅ `SERVICE_TROUBLESHOOTING.md` - Troubleshooting guide (NOVO)
- ✅ `README.md` - Ažurirane upute

## Kontakt

Ako problem i dalje postoji, pošalji:
1. Output od `python service_manager.py install`
2. Sadržaj `app\service_error.log`
3. Output od `sc query SyncBackupService`
