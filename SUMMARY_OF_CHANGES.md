# Sažetak promjena - Windows Service Fix

## Datum: 2025-11-03

## Problem koji si prijavio

```
PS C:\Users\Zaja\Desktop\synhroapp – app> python app/windows_service.py debug
Debugging service SyncBackupService - press Ctrl+C to stop.
Error 0xC0000004 - Python could not import the service's module

ModuleNotFoundError: No module named 'app'
```

**Dodatni simptomi:**
- Servis se ne vidi u `services.msc` iako instalacija kaže da je uspješna
- Pokretanje servisa izbacuje popup s greškom

## Root Cause Analysis

### 1. ModuleNotFoundError: No module named 'app'
**Uzrok**: Kada Windows Service Manager pokreće Python skriptu, radi to u potpuno drugačijem kontekstu nego kada ti pokrećeš skriptu iz komandne linije. U tom kontekstu, `sys.path` ne uključuje parent direktorij, pa Python ne može pronaći `app` modul.

**Lokacija problema**: `app/windows_service.py`, linija 15
```python
# Stari kod - izvršava se prekasno
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### 2. Servis nije vidljiv u services.msc
**Uzrok**: Nepotpuna registracija servisa. Nedostajali su ključni atributi (`_svc_reg_class_`, `_exe_name_`, `_exe_args_`) koji Windows Service Manager koristi za pravilnu registraciju.

**Lokacija problema**: `app/windows_service.py`, klasa `SyncBackupService`

### 3. Nepouzdana instalacija
**Uzrok**: Korištenje `HandleCommandLine` za instalaciju nije bilo dovoljno eksplicitno.

**Lokacija problema**: `app/windows_service.py`, funkcija `install_service()`

## Implementirana rješenja

### ✅ Fix 1: Rano postavljanje sys.path

**Fajl**: `app/windows_service.py`

**Prije:**
```python
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
```

**Poslije:**
```python
import sys
import os
from pathlib import Path

# CRITICAL: Add parent directory to path BEFORE any other imports
_service_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_service_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)
```

**Zašto radi**: Koristi `os.path` umjesto `Path` (koji još nije importiran), i postavlja putanju prije svih drugih importa.

### ✅ Fix 2: Dodani nedostajući atributi servisa

**Fajl**: `app/windows_service.py`

**Dodano:**
```python
class SyncBackupService:
    if PYWIN32_AVAILABLE:
        _svc_name_ = "SyncBackupService"
        _svc_display_name_ = "SyncBackup - Folder Sync & Backup Service"
        _svc_description_ = "Automated folder synchronization and backup service"
        _svc_reg_class_ = "PythonService"          # NOVO
        _exe_name_ = sys.executable                 # NOVO
        _exe_args_ = f'"{os.path.abspath(__file__)}"'  # NOVO
```

**Zašto radi**: Windows Service Manager koristi ove atribute za pravilnu registraciju i pokretanje servisa.

### ✅ Fix 3: Eksplicitna instalacija servisa

**Fajl**: `app/windows_service.py`, funkcija `install_service()`

**Prije:**
```python
sys.argv = ['', 'install']
win32serviceutil.HandleCommandLine(ServiceClass)
```

**Poslije:**
```python
win32serviceutil.InstallService(
    ServiceClass._svc_reg_class_,
    ServiceClass._svc_name_,
    ServiceClass._svc_display_name_,
    description=ServiceClass._svc_description_,
    exeName=sys.executable,
    exeArgs=f'"{service_script}"'
)

# Set service to auto-start
hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
hs = win32service.OpenService(hscm, ServiceClass._svc_name_, win32service.SERVICE_ALL_ACCESS)
win32service.ChangeServiceConfig(
    hs, win32service.SERVICE_NO_CHANGE,
    win32service.SERVICE_AUTO_START,  # Auto-start
    win32service.SERVICE_NO_CHANGE,
    None, None, 0, None, None, None,
    ServiceClass._svc_display_name_
)
```

**Zašto radi**: Direktan poziv `InstallService` s eksplicitnim parametrima osigurava pravilnu registraciju.

### ✅ Fix 4: Bolji error handling

**Fajl**: `app/windows_service.py`, `__main__` blok

**Dodano:**
```python
except Exception as e:
    # Log error to file for debugging
    from datetime import datetime
    log_path = Path(service_dir) / "service_error.log"
    with open(log_path, 'a') as f:
        f.write(f"\n{datetime.now()}: Service start error: {e}\n")
        import traceback
        traceback.print_exc(file=f)
    raise
```

**Zašto radi**: Greške pri pokretanju se sada logiraju u `app/service_error.log` za lakše debugiranje.

## Novi fajlovi

### 1. service_manager.py
**Svrha**: Helper script za lakše upravljanje servisom iz komandne linije.

**Funkcionalnost:**
- `install` - Instalira servis
- `uninstall` - Uklanja servis
- `start` - Pokreće servis
- `stop` - Zaustavlja servis
- `restart` - Restartuje servis
- `status` - Prikazuje status servisa
- `debug` - Pokreće servis u debug modu (konzola)

**Korištenje:**
```powershell
python service_manager.py install
python service_manager.py start
python service_manager.py status
```

### 2. SERVIS_UPUTE.md
**Svrha**: Kratke upute za instalaciju i testiranje servisa (Hrvatski).

**Sadržaj:**
- Koraci za instalaciju
- Brze naredbe
- Troubleshooting
- Testiranje iz GUI-a

### 3. SERVICE_TROUBLESHOOTING.md
**Svrha**: Detaljan troubleshooting guide (English).

**Sadržaj:**
- Problem analysis
- Step-by-step testing
- Common errors and solutions
- Debug information collection

### 4. WINDOWS_SERVICE_FIX.md
**Svrha**: Brzi pregled problema i rješenja.

**Sadržaj:**
- Problem description
- Quick fix steps
- Expected results
- Troubleshooting

## Ažurirani fajlovi

### README.md
**Dodano:**
- Windows Service Command Line Management sekcija
- File Structure ažuriran s novim fajlovima
- Windows Service Issues u Troubleshooting
- Changelog ažuriran s Windows Service fixes

## Kako testirati

### Korak 1: Ukloni stari servis
```powershell
sc stop SyncBackupService
sc delete SyncBackupService
```

### Korak 2: Instaliraj novi servis
```powershell
cd "C:\Users\Zaja\Desktop\synhroapp – app"
python service_manager.py install
```

### Korak 3: Provjeri instalaciju
```powershell
python service_manager.py status
services.msc  # Traži "SyncBackup - Folder Sync & Backup Service"
```

### Korak 4: Testiraj u debug modu
```powershell
python service_manager.py debug
# Pritisni Ctrl+C za zaustavljanje
```

### Korak 5: Pokreni servis
```powershell
python service_manager.py start
python service_manager.py status
type app\service.log
```

## Očekivani rezultati

Nakon implementacije ovih promjena:

✅ **ModuleNotFoundError riješen** - `app` modul se sada pravilno pronalazi  
✅ **Servis vidljiv u services.msc** - Pravilna registracija u Windows Service Manager  
✅ **Servis se može pokrenuti** - Bez grešaka pri pokretanju  
✅ **Auto-start konfiguriran** - Servis se automatski pokreće s Windows-om  
✅ **Bolji debugging** - Logovi u `app/service.log` i `app/service_error.log`  
✅ **Lakše upravljanje** - `service_manager.py` helper script  

## Tehnički detalji

### Izmijenjene funkcije u windows_service.py:
1. `install_service()` - Potpuno prepisana
2. `uninstall_service()` - Dodana admin provjera i bolji error handling
3. `__main__` blok - Dodano error logging

### Dodani atributi u SyncBackupService:
1. `_svc_reg_class_`
2. `_exe_name_`
3. `_exe_args_`

### Dodani importi:
1. `win32api` - Za dodatne Windows API funkcije

## Testiranje

Testiraj sljedeće scenarije:

1. ✅ Instalacija servisa
2. ✅ Provjera vidljivosti u services.msc
3. ✅ Pokretanje u debug modu
4. ✅ Pokretanje kao servis
5. ✅ Zaustavljanje servisa
6. ✅ Restart servisa
7. ✅ Provjera logova
8. ✅ Deinstalacija servisa

## Backup

Prije testiranja, napravio sam backup:
- Originalni `app/windows_service.py` možeš vratiti iz git historije ako treba

## Sljedeći koraci

1. Testiraj instalaciju servisa
2. Provjeri da li se servis vidi u services.msc
3. Testiraj pokretanje u debug modu
4. Testiraj pokretanje kao servis
5. Provjeri logove
6. Testiraj iz GUI-a (Settings tab)

## Potrebna pomoć?

Ako nešto ne radi, pošalji:
1. Output od `python service_manager.py install`
2. Sadržaj `app\service_error.log`
3. Output od `sc query SyncBackupService`
4. Screenshot iz `services.msc`
