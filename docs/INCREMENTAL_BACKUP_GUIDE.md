# Incremental Backup - Korisnički Vodič

## Što je Incremental Backup?

Incremental backup je metoda backup-a koja čuva samo **promijenjene datoteke** između backup-a, umjesto kopiranja svih datoteka svaki put.

## Kako Radi?

### 1. Prvi Backup (Inicijalni)
Kada prvi put pokrenete incremental backup job, aplikacija:
- Kreira folder sa nazivom: `{naziv_foldera}_INCREMENTAL_INICIAL_{datum_vrijeme}`
- Kopira **sve datoteke** iz izvora
- Ovo je vaš "bazni" backup

**Primjer:**
```
Projekt_INCREMENTAL_INICIAL_20251108_140000/
├── dokument1.docx
├── dokument2.pdf
├── slika1.jpg
└── ...sve ostale datoteke
```

### 2. Sljedeći Backupi (Incrementalni)
Svaki sljedeći put kada se backup pokrene:
- Uspoređuje trenutno stanje sa **zadnjim backupom**
- Kreira novi folder: `{naziv_foldera}_INCREMENTAL_{datum_vrijeme}`
- Kopira **samo izmijenjene ili nove datoteke**

**Primjer:**
```
Projekt_INCREMENTAL_20251108_150000/
├── dokument1.docx  (promijenjen)
└── dokument3.pdf   (novi)
```

### 3. Ako Nema Promjena
- Ako nema izmjena, **ne kreira se novi folder**
- U logu će pisati: "No changes detected, skipping incremental backup"

## Prednosti

### 💾 Ušteda Prostora
- Samo izmijenjene datoteke se kopiraju
- Manji backup folderi
- Optimalno za velike projekte sa malim izmjenama

**Primjer:**
- Projekt: 10 GB (1000 datoteka)
- Promijenjeno: 5 datoteka (50 MB)
- Backup veličina: **50 MB** umjesto 10 GB

### 📜 Povijest Promjena
- Svaki backup je samostalan folder
- Možete vidjeti što se promijenilo i kada
- Lako vraćanje na određenu verziju

### ⚡ Brži Backup
- Kopira se manje datoteka
- Brže izvršavanje
- Manje opterećenje diska

## Kako Koristiti?

### Kreiranje Incremental Job-a

1. **Otvori aplikaciju** → Klikni "Add New Job"

2. **Odaberi tip**: `Incremental`

3. **Postavi putanje**:
   - **Source Path**: Folder koji želiš backup-ati
   - **Destination Path**: Gdje će se čuvati backup-i

4. **Opcije**:
   - **Preserve Deleted**: Ako je uključeno, obrisane datoteke ostaju u backupu
   - **Schedule**: Postavi kada se backup pokreće (Daily, Weekly, Monthly)

5. **Klikni "Save"**

### Praćenje Backup-a

U **Dashboard** tabu možeš vidjeti:
- Status svakog job-a
- Zadnji backup
- Broj datoteka
- Veličinu backup-a

### Pregled Backup-a

U **Backups** tabu možeš vidjeti:
- Sve kreirane backup foldere
- Datum i vrijeme svakog backupa
- Veličinu svakog backupa
- Tip backupa (INICIAL ili INCREMENTAL)

## Vraćanje Datoteka

### Vraćanje Pojedinačne Datoteke

1. Pronađi backup folder u destinaciji
2. Otvori folder
3. Kopiraj datoteku koju trebaš

### Vraćanje Cijelog Projekta

**Metoda 1: Kombiniraj sve backupe**
1. Kopiraj INICIAL folder
2. Prepiši sa datotekama iz svakog INCREMENTAL foldera (po redu)

**Metoda 2: Koristi najnoviji backup**
- Ako trebaš samo najnovije stanje, kopiraj zadnji INCREMENTAL folder
- Ali moraš imati i INICIAL folder za datoteke koje nisu promijenjene

## Najbolje Prakse

### ✅ Preporuke

1. **Redoviti Backupi**
   - Postavi automatski schedule (npr. svaki dan)
   - Tako imaš povijest promjena

2. **Retention Policy**
   - Postavi koliko backupa želiš zadržati
   - Automatski briše stare backupe

3. **Testiranje**
   - Povremeno testiraj vraćanje datoteka
   - Provjeri da backupi rade kako treba

4. **Exclude Patterns**
   - Isključi privremene datoteke (`.tmp`, `~$*`)
   - Isključi cache foldere (`node_modules`, `__pycache__`)

### ❌ Izbjegavaj

1. **Ne mijenjaj backup foldere ručno**
   - Aplikacija se oslanja na strukturu foldera
   - Ručne izmjene mogu poremetiti logiku

2. **Ne brišite INICIAL backup**
   - To je bazni backup
   - Bez njega ne možeš potpuno vratiti projekt

3. **Ne koristite za velike binarne datoteke koje se često mijenjaju**
   - Video datoteke, baze podataka, VM diskovi
   - Za to koristi druge backup metode

## Usporedba sa Drugim Tipovima

### Simple Backup
- Kopira sve datoteke svaki put
- Jednostavniji, ali zauzima više prostora
- Bolji za male projekte

### Incremental Backup
- Kopira samo izmjene
- Kompleksniji, ali efikasniji
- Bolji za velike projekte sa malim izmjenama

## Primjeri Korištenja

### 1. Razvoj Softvera
```
Projekt: 5 GB (10,000 datoteka)
Dnevne izmjene: 20-50 datoteka (~10 MB)

Rezultat:
- INICIAL: 5 GB
- Svaki dan: ~10 MB
- Mjesečno: ~300 MB umjesto 150 GB
```

### 2. Dokumenti
```
Folder: 2 GB (500 dokumenata)
Dnevne izmjene: 5-10 dokumenata (~5 MB)

Rezultat:
- INICIAL: 2 GB
- Svaki dan: ~5 MB
- Mjesečno: ~150 MB umjesto 60 GB
```

### 3. Fotografije
```
Folder: 50 GB (5,000 fotografija)
Novi dodaci: 10-20 fotografija tjedno (~100 MB)

Rezultat:
- INICIAL: 50 GB
- Svaki tjedan: ~100 MB
- Mjesečno: ~400 MB umjesto 200 GB
```

## Troubleshooting

### Problem: "No changes detected" ali znam da ima promjena

**Rješenje:**
- Provjeri da datoteke imaju noviji modification time
- Neki programi ne ažuriraju modification time
- Pokušaj "touch" datoteku ili je ponovno spremi

### Problem: Backup folder je prazan

**Rješenje:**
- Provjeri exclude patterns
- Možda su sve datoteke isključene
- Provjeri log za detalje

### Problem: Backup je prespor

**Rješenje:**
- Provjeri broj datoteka
- Koristi exclude patterns za privremene datoteke
- Razmotri Simple backup za male projekte

## Dodatne Informacije

Za više informacija, pogledaj:
- `INCREMENTAL_BACKUP_CHANGELOG.md` - Tehnički detalji
- `README.md` - Opći vodič za aplikaciju
- Log datoteke u `app/logs/` - Detalji o izvršavanju
