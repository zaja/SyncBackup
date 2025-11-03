# SyncBackup v1.3 - Quick Start Guide

## 🚀 Brzi Start

### 1. Pokretanje Aplikacije

```bash
# Normalno pokretanje (sa konzolom)
python main.py

# GUI mode bez konzole (Windows)
pythonw main.py
```

### 2. Testiranje Novih Funkcionalnosti

```bash
# Pokreni test script
python test_v1.3_features.py
```

## ⚙️ Nove Funkcionalnosti v1.3

### 🔔 Notification Batching

**Problem riješen:** Više nema 20+ notifikacija koje iskaču jedna za drugom!

**Kako koristiti:**
1. Otvori aplikaciju
2. Klikni na tab **"⚙️ Settings"**
3. U sekciji **"Notification Settings"** odaberi:
   - **Batch** (preporučeno) - Grupira notifikacije
   - **Immediate** - Prikazuje odmah (staro ponašanje)
   - **Disabled** - Bez notifikacija
4. Ako odabereš Batch, postavi interval (default: 300s = 5min)
5. Klikni **"💾 Save Settings"**

**Kako radi Batch mode:**
- Umjesto da svaki backup prikaže notifikaciju odmah, sustav ih sprema
- Svakih N sekundi (default 5 minuta) prikazuje se JEDNA sažeta notifikacija
- Primjer: "📊 Backup Summary (15 jobs): ✅ 12 completed, ❌ 2 failed, ⏸️ 1 skipped"

### 🔧 Windows Service

**Novo:** Aplikacija može raditi kao Windows Service!

**Prednosti:**
- Radi u pozadini bez korisničkog logina
- Automatski start sa Windowsima
- Idealno za server/NAS backup scenarije

**Instalacija:**

1. **Instaliraj pywin32:**
   ```bash
   pip install pywin32
   ```

2. **Pokreni aplikaciju kao Administrator**
   - Desni klik na main.py → Run as administrator
   - Ili pokreni Command Prompt kao admin pa: `python main.py`

3. **U aplikaciji:**
   - Idi na **Settings** tab
   - U sekciji **"Windows Service Settings"**
   - Klikni **"Install Service"**
   - Potvrdi instalaciju

4. **Provjeri status:**
   - Klikni **"Service Status"**
   - Ili otvori Windows Services (Win+R → services.msc)
   - Pronađi "SyncBackup - Folder Sync & Backup Service"

5. **Pokreni servis:**
   - U Windows Services, desni klik → Start
   - Ili iz aplikacije (buduća verzija)

**Deinstalacija:**
- Settings tab → "Uninstall Service"
- Mora biti pokrenut kao Administrator

### 🌐 Language Selection

**Novo:** Odabir jezika (priprema za lokalizaciju)

**Kako koristiti:**
1. Settings tab
2. Sekcija **"Language / Jezik"**
3. Odaberi: Hrvatski (Croatian) ili English
4. Klikni **"Save Settings"**
5. Restartaj aplikaciju

**Napomena:** Trenutno samo sprema odabir. Puna lokalizacija stiže u budućoj verziji.

## 📊 Primjeri Korištenja

### Scenario 1: Dnevni Backup s Batch Notifikacijama

**Setup:**
1. Kreiraj job koji radi svaki dan u 2:00 AM
2. Postavi Batch mode s intervalom 300s (5min)
3. Ako imaš više jobova koji rade noću, ujutro ćeš dobiti JEDNU notifikaciju sa sažetkom

**Rezultat:**
- Umjesto 10 notifikacija ujutro → 1 sažeta notifikacija
- Vidiš odmah koliko je uspjelo, koliko failalo

### Scenario 2: Server Backup sa Service Mode

**Setup:**
1. Instaliraj pywin32
2. Instaliraj SyncBackup kao Service
3. Konfiguriraj jobove
4. Postavi Disabled notifications (server nema GUI)
5. Pokreni service

**Rezultat:**
- Backupi rade automatski 24/7
- Nema potrebe za korisničkim loginom
- Sve logovi u bazi podataka

### Scenario 3: Development Machine s Immediate Notifikacijama

**Setup:**
1. Postavi Immediate mode
2. Kreiraj jobove za važne projekte
3. Dobij instant feedback kada se backup završi

**Rezultat:**
- Odmah znaš kada je backup gotov
- Vidiš eventualne greške odmah

## 🧪 Testiranje

### Test 1: Batch Notifications (5 minuta)

```bash
# 1. Postavi batch mode s intervalom 60s (za brže testiranje)
# 2. Kreiraj 3 test joba koji rade svake 2 minute
# 3. Pričekaj da se izvrše
# 4. Nakon 60s trebala bi se pojaviti jedna sažeta notifikacija
```

### Test 2: Settings Persistence

```bash
# 1. Promijeni settings
# 2. Klikni Save
# 3. Zatvori aplikaciju
# 4. Pokreni ponovno
# 5. Provjeri da su settings sačuvani
```

### Test 3: Windows Service (Samo Windows)

```bash
# 1. Instaliraj pywin32
pip install pywin32

# 2. Pokreni kao admin
# 3. Install Service
# 4. Otvori services.msc
# 5. Pronađi "SyncBackup" servis
# 6. Pokreni ga
# 7. Provjeri status
```

## 🔍 Troubleshooting

### Problem: Batch notifikacije se ne pojavljuju

**Rješenje:**
1. Provjeri da je Batch mode odabran u Settings
2. Provjeri da postoje pending notifikacije (pokreni neki job)
3. Pričekaj batch interval (default 5min)
4. Provjeri konzolu za errore

### Problem: Service se ne instalira

**Rješenje:**
1. Provjeri da je pywin32 instaliran: `pip list | findstr pywin32`
2. Provjeri da aplikacija radi kao Administrator
3. Provjeri Windows Event Log za detalje

### Problem: Settings se ne spremaju

**Rješenje:**
1. Provjeri da baza nije read-only
2. Provjeri permissions na `app/sync_backup.db`
3. Provjeri konzolu za SQL errore

## 📝 Changelog v1.3

- ✅ Notification Batching (3 moda: Immediate, Batch, Disabled)
- ✅ Windows Service Support (install/uninstall/status)
- ✅ Settings Tab (language, notifications, service)
- ✅ Database schema updates (app_settings, notification_queue)
- ✅ Batch notification processor thread
- ✅ Service management GUI

## 🔗 Korisni Linkovi

- **Dokumentacija:** README.md
- **Detaljne izmjene:** CHANGES_v1.3.md
- **Test script:** test_v1.3_features.py
- **Website:** https://svejedobro.hr

## 💡 Tips & Tricks

1. **Batch interval:** Za testiranje postavi na 60s, za produkciju 300s (5min)
2. **Service mode:** Idealno za servere i NAS uređaje
3. **Immediate mode:** Dobro za development i testiranje
4. **Disabled mode:** Ako koristiš samo logove, bez notifikacija

## ⚠️ Važne Napomene

- Windows Service zahtijeva **pywin32** (opcionalno)
- Service instalacija zahtijeva **Admin privilegije**
- Language selection trenutno samo sprema odabir (lokalizacija dolazi)
- Batch interval promjena zahtijeva **restart aplikacije**

---

**Verzija:** 1.3  
**Datum:** 3. Studeni 2025  
**Autor:** Goran Zajec
