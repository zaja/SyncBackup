# Windows Servis - Upute za instalaciju i testiranje

## Što sam popravio

Identificirao sam i popravio **3 glavna problema**:

1. **Python putanje** - Servis nije mogao pronaći `app` modul
2. **Registracija servisa** - Servis se nije pravilno registrirao u Windows-u
3. **Nedostajući atributi** - Servisu su nedostajali potrebni atributi za pokretanje

## Kako testirati

### 1. Ukloni stari servis (ako postoji)

Otvori **PowerShell kao Administrator**:

```powershell
sc stop SyncBackupService
sc delete SyncBackupService
```

### 2. Instaliraj novi servis

```powershell
cd "C:\Users\Zaja\Desktop\synhroapp – app"
python service_manager.py install
```

Trebao bi vidjeti poruku o uspješnoj instalaciji.

### 3. Provjeri je li servis vidljiv

```powershell
# Provjeri status
python service_manager.py status

# Ili otvori Services Manager
services.msc
```

U `services.msc` traži **"SyncBackup - Folder Sync & Backup Service"**

### 4. Testiraj u debug modu (opciono)

Prije pokretanja kao servis, testiraj da logika radi:

```powershell
python service_manager.py debug
```

Pritisni Ctrl+C za zaustavljanje.

### 5. Pokreni servis

```powershell
python service_manager.py start
```

### 6. Provjeri da li radi

```powershell
# Provjeri status
python service_manager.py status

# Pogledaj log
type app\service.log
```

## Brze naredbe

```powershell
# Instaliraj
python service_manager.py install

# Pokreni
python service_manager.py start

# Zaustavi
python service_manager.py stop

# Status
python service_manager.py status

# Ukloni
python service_manager.py uninstall

# Debug mod
python service_manager.py debug
```

## Ako nešto ne radi

### Greška: "Access Denied"
→ Pokreni PowerShell kao Administrator

### Greška: "Service already exists"
→ Prvo ukloni stari: `sc delete SyncBackupService`

### Servis se ne vidi u popisu
→ Provjeri `app\service_error.log`

### Servis se ne pokreće
→ Pokreni u debug modu: `python service_manager.py debug`

## Testiranje iz GUI-a

Nakon što potvrdiš da servis radi iz komandne linije:

1. Pokreni `python main.py`
2. Idi na **Settings** tab
3. Klikni **Service Status** - trebao bi vidjeti status
4. Testiraj **Start Service** / **Stop Service**

## Logovi

Servis piše logove u:
- `app\service.log` - normalni rad
- `app\service_error.log` - greške

```powershell
# Prati log u realnom vremenu
Get-Content app\service.log -Wait
```

## Napomena

Servis mora biti pokrenut kao **Administrator** jer radi s Windows Service Manager-om.
