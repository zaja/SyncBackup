# Windows Service - Troubleshooting Guide

## Problem koji si primijetio

1. **Servis se ne vidi u popisu servisa** - iako instalacija kaže da je uspješna
2. **Greška pri pokretanju**: `ModuleNotFoundError: No module named 'app'`

## Što je bilo krivo

### Problem 1: Python putanje
Kada Windows servis pokreće Python skriptu, radi se u drugačijem kontekstu nego kada pokrećeš skriptu normalno. `sys.path` ne uključuje automatski parent direktorij, pa Python ne može pronaći `app` modul.

**Riješeno**: Dodao sam eksplicitno postavljanje `sys.path` na samom početku `windows_service.py` prije svih importa.

### Problem 2: Registracija servisa
Prethodna implementacija koristila je `HandleCommandLine` što nije uvijek pouzdano. 

**Riješeno**: Sada koristim `InstallService` direktno s eksplicitnim parametrima.

### Problem 3: Nedostajući atributi servisa
Servisu su nedostajali `_svc_reg_class_`, `_exe_name_` i `_exe_args_` atributi koji su potrebni za pravilnu registraciju.

**Riješeno**: Dodao sam sve potrebne atribute.

## Kako testirati popravke

### Korak 1: Ukloni stari servis (ako postoji)

Otvori PowerShell **kao Administrator** i pokreni:

```powershell
# Provjeri postoji li servis
sc query SyncBackupService

# Ako postoji, zaustavi ga
sc stop SyncBackupService

# Obriši ga
sc delete SyncBackupService
```

### Korak 2: Instaliraj novi servis

Koristi novi `service_manager.py` helper script:

```powershell
# U PowerShell-u kao Administrator, u folderu aplikacije:
python service_manager.py install
```

Trebao bi vidjeti detaljne informacije o instalaciji.

### Korak 3: Provjeri je li servis instaliran

```powershell
# Provjeri status
python service_manager.py status

# Ili direktno u Windows-u
sc query SyncBackupService

# Ili otvori Services Manager
services.msc
# Traži "SyncBackup - Folder Sync & Backup Service"
```

### Korak 4: Testiraj pokretanje u debug modu

Prije nego pokreneš servis, testiraj ga u debug modu da vidiš radi li logika:

```powershell
python service_manager.py debug
```

Ovo će pokrenuti servis u konzoli gdje možeš vidjeti sve outpute. Pritisni Ctrl+C za zaustavljanje.

### Korak 5: Pokreni servis

```powershell
# Pokreni servis
python service_manager.py start

# Provjeri status
python service_manager.py status

# Provjeri log fajl
type app\service.log
```

### Korak 6: Zaustavi servis

```powershell
python service_manager.py stop
```

## Alternativni način - Korištenje pywin32 alata

Ako `service_manager.py` ne radi, možeš koristiti direktno pywin32 alate:

```powershell
# Instaliraj
python app\windows_service.py install

# Pokreni
python app\windows_service.py start

# Zaustavi
python app\windows_service.py stop

# Ukloni
python app\windows_service.py remove
```

## Provjera logova

Servis zapisuje logove u:
- `app\service.log` - normalni logovi
- `app\service_error.log` - greške pri pokretanju

```powershell
# Pogledaj logove
type app\service.log
type app\service_error.log
```

## Česte greške i rješenja

### "Access Denied"
**Uzrok**: Nemaš admin privilegije  
**Rješenje**: Pokreni PowerShell kao Administrator

### "Service already exists"
**Uzrok**: Stari servis još postoji  
**Rješenje**: Prvo ga ukloni s `sc delete SyncBackupService`

### "The service did not respond to the start or control request in a timely fashion"
**Uzrok**: Servis se ruši pri pokretanju  
**Rješenje**: Provjeri `app\service_error.log` za detalje

### "ModuleNotFoundError: No module named 'app'"
**Uzrok**: Python putanje nisu pravilno postavljene  
**Rješenje**: Ova greška bi sada trebala biti riješena novim kodom

## Testiranje iz GUI-a

Nakon što potvrdiš da servis radi iz komandne linije:

1. Pokreni `main.py`
2. Idi na **Settings** tab
3. Scroll dolje do **Windows Service** sekcije
4. Klikni **Service Status** - trebao bi vidjeti "Running" ili "Stopped"
5. Testiraj **Start Service** / **Stop Service** gumbe

## Provjera da li servis stvarno radi

Kada je servis pokrenut:

1. Kreiraj test job u GUI-u s kratkim intervalom (npr. svake minute)
2. Zatvori GUI aplikaciju
3. Pričekaj da prođe vrijeme
4. Otvori GUI ponovno i provjeri **Log Viewer** - trebao bi vidjeti da je job izvršen

## Debug informacije

Ako i dalje imaš problema, prikupi ove informacije:

```powershell
# Python verzija
python --version

# Provjeri je li pywin32 instaliran
pip show pywin32

# Provjeri sys.path
python -c "import sys; print('\n'.join(sys.path))"

# Provjeri može li se importati app modul
cd "C:\Users\Zaja\Desktop\synhroapp – app"
python -c "import app.database; print('OK')"

# Provjeri Windows Event Log
eventvwr.msc
# Navigate to: Windows Logs > Application
# Traži događaje od "SyncBackupService"
```

## Kontakt za pomoć

Ako problem i dalje postoji, pošalji:
1. Output od `python service_manager.py install`
2. Sadržaj `app\service_error.log`
3. Output od `sc query SyncBackupService`
4. Screenshot iz `services.msc`
