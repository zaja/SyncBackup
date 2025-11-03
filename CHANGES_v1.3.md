# SyncBackup v1.3 - Izmjene i Poboljšanja

## Datum: 3. Studeni 2025

## 📋 Pregled Izmjena

Implementirane su tri glavne izmjene prema zahtjevima:

### 1. ✅ Rješenje za Gomilanje Notifikacija

**Problem:** Kada korisnik nije bio na računalu, nakupi se 20+ notifikacija koje iskaču jedna za drugom.

**Rješenje:** Implementiran sustav grupiranja notifikacija s tri moda rada:

#### Notification Modes:
- **Immediate Mode** - Prikazuje notifikaciju za svaki backup odmah nakon završetka
- **Batch Mode** (Default) - Grupira notifikacije i prikazuje sažetak svakih 5 minuta
- **Disabled** - Bez notifikacija

#### Kako Batch Mode Funkcionira:
1. Umjesto trenutnog prikazivanja, notifikacije se spremaju u queue (bazu podataka)
2. Svaki N sekundi (konfigurirano, default 300s = 5min) sustav provjerava queue
3. Ako ima pending notifikacija, prikazuje se JEDNA sažeta notifikacija:
   - "📊 Backup Summary (15 jobs)"
   - "✅ 12 completed"
   - "❌ 2 failed"
   - "⏸️ 1 skipped"
   - "Failed: Job1, Job2"

#### Tehnička Implementacija:
- Nova tablica u bazi: `notification_queue`
- Novi thread: `notification_processor_loop()` koji radi paralelno sa schedulером
- Metoda `send_batch_notification()` koja agregira rezultate
- Automatsko čišćenje starih notifikacija (7 dana)

### 2. ✅ Windows Service Podrška

**Zahtjev:** Mogućnost pokretanja aplikacije kao Windows Service

**Implementacija:**
- Novi modul: `app/windows_service.py`
- Koristi `pywin32` biblioteku (opcionalna ovisnost)
- Service klasa: `SyncBackupService`

#### Funkcionalnosti:
- **Install Service** - Instalacija kao Windows Service
- **Uninstall Service** - Deinstalacija servisa
- **Service Status** - Provjera statusa servisa
- **Auto-start** - Automatsko pokretanje sa Windowsima
- **Background Operation** - Rad u pozadini bez korisničkog logina

#### Sigurnosne Provjere:
- Provjera admin privilegija prije instalacije/deinstalacije
- Provjera dostupnosti pywin32 biblioteke
- Graceful degradation ako pywin32 nije instaliran

#### Korištenje:
```bash
# Instalacija pywin32 (opcionalno)
pip install pywin32

# Instalacija servisa (kao administrator)
python app/windows_service.py install

# Pokretanje servisa
python app/windows_service.py start

# Zaustavljanje servisa
python app/windows_service.py stop

# Deinstalacija servisa
python app/windows_service.py remove
```

### 3. ✅ Settings Tab

**Zahtjev:** Tab za postavke s opcijama za servis i jezik

**Implementacija:**
Novi tab "⚙️ Settings" s tri sekcije:

#### A. Language / Jezik
- Radio buttons: Hrvatski (Croatian) / English
- Napomena: Promjena jezika zahtijeva restart aplikacije
- Spremljeno u bazu podataka

#### B. Notification Settings
- **Notification mode**: Immediate / Batch / Disabled
- **Batch interval**: Spinbox (60-3600 sekundi)
- Objašnjenje batch moda
- Spremljeno u bazu podataka

#### C. Windows Service Settings (samo na Windows OS)
- Checkbox: "Enable Windows Service mode"
- Tri buttona:
  - **Install Service** - Instalira servis
  - **Uninstall Service** - Deinstalira servis
  - **Service Status** - Prikazuje status servisa
- Napomene o admin privilegijama
- Spremljeno u bazu podataka

#### Save Button:
- Sprema sve postavke u bazu
- Prikazuje poruku o uspjehu
- Upozorava da neke postavke zahtijevaju restart

## 🗄️ Izmjene u Bazi Podataka

### Nova Tablica: `app_settings`
```sql
CREATE TABLE app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Default postavke:**
- `language`: 'hr'
- `run_as_service`: '0'
- `notification_mode`: 'batch'
- `notification_batch_interval`: '300'

### Nova Tablica: `notification_queue`
```sql
CREATE TABLE notification_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    job_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'error', 'skipped')),
    message TEXT,
    files_processed INTEGER DEFAULT 0,
    duration_seconds REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    sent BOOLEAN DEFAULT 0,
    FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
)
```

### Nove Metode u DatabaseManager:
- `get_setting(key, default)` - Dohvat postavke
- `set_setting(key, value)` - Spremanje postavke
- `get_all_settings()` - Dohvat svih postavki
- `add_notification_to_queue()` - Dodavanje notifikacije u queue
- `get_pending_notifications()` - Dohvat pending notifikacija
- `mark_notifications_as_sent()` - Označavanje kao poslano
- `cleanup_old_notifications()` - Čišćenje starih notifikacija

## 📝 Izmjene u Glavnoj Aplikaciji (main.py)

### Nove Metode:
1. `create_settings_tab()` - Kreiranje Settings taba
2. `save_settings()` - Spremanje postavki
3. `install_service()` - Instalacija Windows servisa
4. `uninstall_service()` - Deinstalacija servisa
5. `check_service_status()` - Provjera statusa servisa
6. `start_notification_processor()` - Pokretanje notification processora
7. `notification_processor_loop()` - Loop za batch notifikacije
8. `send_batch_notification()` - Slanje batch notifikacije

### Izmijenjene Metode:
- `notify_job_result()` - Sada podržava batch mode
- `on_close()` - Zaustavlja i notification processor
- `run()` - Zaustavlja notification processor pri izlasku

### Novi Thread:
- `notification_thread` - Radi paralelno, provjerava queue svakih N sekundi

## 📦 Novi Fajlovi

1. **app/windows_service.py** - Windows Service wrapper
2. **CHANGES_v1.3.md** - Ovaj dokument

## 🔄 Izmijenjeni Fajlovi

1. **main.py** - Dodane nove funkcionalnosti
2. **app/database.py** - Nove tablice i metode
3. **app/requirements.txt** - Dodan pywin32 kao opcionalna ovisnost
4. **README.md** - Dokumentacija novih funkcionalnosti

## 🎯 Kako Testirati

### Test 1: Notification Batching
1. Pokreni aplikaciju
2. Idi na Settings tab
3. Odaberi "Batch" mode
4. Postavi interval na 60 sekundi (za brže testiranje)
5. Klikni "Save Settings"
6. Kreiraj nekoliko jobova s kratkim intervalima (npr. svake 2 minute)
7. Pričekaj da se izvrši više jobova
8. Nakon 60 sekundi trebala bi se pojaviti JEDNA sažeta notifikacija

### Test 2: Settings Tab
1. Pokreni aplikaciju
2. Idi na Settings tab
3. Promijeni jezik na English
4. Promijeni notification mode
5. Promijeni batch interval
6. Klikni "Save Settings"
7. Provjeri da je poruka o uspjehu prikazana
8. Restartaj aplikaciju i provjeri da su postavke sačuvane

### Test 3: Windows Service (Samo Windows, kao Administrator)
1. Instaliraj pywin32: `pip install pywin32`
2. Pokreni aplikaciju kao administrator
3. Idi na Settings tab
4. Klikni "Install Service"
5. Potvrdi instalaciju
6. Klikni "Service Status" - trebalo bi pisati "Stopped" ili "Running"
7. Otvori Windows Services (services.msc)
8. Pronađi "SyncBackup - Folder Sync & Backup Service"
9. Pokreni servis
10. Provjeri status ponovno

### Test 4: Notification Modes
1. **Immediate Mode:**
   - Postavi na Immediate
   - Pokreni job ručno
   - Trebala bi se odmah pojaviti notifikacija

2. **Batch Mode:**
   - Postavi na Batch
   - Pokreni više jobova
   - Pričekaj batch interval
   - Trebala bi se pojaviti jedna sažeta notifikacija

3. **Disabled Mode:**
   - Postavi na Disabled
   - Pokreni job
   - Ne bi se trebala pojaviti nikakva notifikacija

## ⚠️ Napomene

### Kompatibilnost:
- Windows Service funkcionalnost radi SAMO na Windows OS-u
- Zahtijeva pywin32 biblioteku (opcionalno)
- Bez pywin32, aplikacija normalno radi ali bez service funkcionalnosti

### Sigurnost:
- Service instalacija/deinstalacija zahtijeva admin privilegije
- Aplikacija provjerava admin status prije pokušaja instalacije

### Performance:
- Notification processor thread koristi minimalne resurse
- Spava između provjera (default 5 minuta)
- Automatski cleanup starih notifikacija sprječava rast baze

### Backward Compatibility:
- Postojeći jobovi nastavljaju raditi normalno
- Stara baza se automatski migrira (dodaju se nove tablice)
- Default postavke osiguravaju da sve radi "out of the box"

## 🐛 Poznati Problemi / Ograničenja

1. **Language Selection:**
   - Trenutno samo sprema odabir jezika
   - Stvarna lokalizacija UI-a nije implementirana
   - Potrebno dodati translation fajlove u budućnosti

2. **Windows Service:**
   - Service trenutno samo logira kada bi trebao pokrenuti jobove
   - Puna integracija s job execution engineom za buduću verziju
   - Zahtijeva dodatno testiranje na različitim Windows verzijama

3. **Notification Batching:**
   - Batch interval se primjenjuje tek nakon restarta notification processora
   - Za promjenu intervala potreban je restart aplikacije

## 🔮 Buduća Poboljšanja

1. Puna lokalizacija UI-a (hrvatski/engleski)
2. Kompletnija Windows Service integracija
3. Dinamička promjena batch intervala bez restarta
4. Email notifikacije kao dodatna opcija
5. Notification history viewer
6. Service logs viewer u GUI-u

## 📞 Podrška

Za pitanja ili probleme, kontaktirajte:
- **Autor:** Goran Zajec
- **Website:** https://svejedobro.hr

---

**Verzija:** 1.3  
**Datum:** 3. Studeni 2025  
**Status:** ✅ Implementirano i testirano
