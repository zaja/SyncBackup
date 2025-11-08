# SyncBackup v1.5 - True Incremental Backups & Major Improvements

## 🎉 Major Release

This release introduces **true incremental backup system** with smart change detection, **chain-based retention policy**, and **preserve deleted files** functionality.

---

## 🌟 Key Features

### ✨ True Incremental Backups
- **INICIAL backups**: Full baseline with all files
- **Incremental backups**: Only changed/new files
- **Smart detection**: Uses modification time and file size
- **Separate folders**: Each backup independent

### 🔄 Reset Chain After N Incrementals
- Auto-create new INICIAL after N incrementals
- Prevents long restore chains
- Configurable per job (0 = never)

### 💾 Preserve Deleted Files
- Marks deleted files with `_DELETED` suffix
- Easy recovery: remove suffix
- Prevents data loss

### 🗑️ Chain-Based Retention Policy
- **Incremental**: Deletes entire chains
- **Simple**: Deletes individual backups
- Simplified to "Keep N" only
- Auto-cleanup after each backup

### 📊 Dashboard Improvements
- Larger Recent Activity (15 lines)
- More details (date, time, status, files)
- Better format (columnar layout)
- More history (30 entries)

### 🔧 Windows Service
- Full support for all new features
- Improved logging
- Better reliability

---

## 📦 What's Included

- Windows executable (no Python required)
- Full source code
- Documentation (README, Manual, Changelog)
- Migration script (for v1.4 users)

---

## 🚀 Installation

### New Users:
1. Download `SyncBackup_v1.5.zip`
2. Extract to desired location
3. Run `main.pyw` or `main.py`
4. Configure your first backup job

### Upgrading from v1.4:
1. Backup your database: `app/sync_backup.db`
2. Download and extract v1.5
3. Copy your old database to new installation
4. Run `migrate_reset_chain_after.py`
5. Review and adjust job settings

---

## 📋 System Requirements

- Windows 10/11
- Python 3.8+ (if running from source)
- 100 MB free disk space
- Administrator privileges (for Windows Service)

---

## 🐛 Bug Fixes

- Fixed duplicate INICIAL backups
- Fixed database CHECK constraints
- Improved retention policy
- Better edge case handling

---

## 📝 Documentation

- [README.md](README.md) - Full documentation
- [CHANGELOG_v1.5.md](CHANGELOG_v1.5.md) - Detailed changelog
- [MANUAL_EN.html](docs/MANUAL_EN.html) - User manual

---

## ⚠️ Breaking Changes

- Snapshot feature removed (replaced with reset_chain_after)
- Retention policy simplified (only "Keep N")
- Database migration required for v1.4 users

---

## 🙏 Credits

**Author**: Goran Zajec  
**Website**: https://svejedobro.hr

Thank you to all users who provided feedback!

---

## 📥 Downloads

- **Windows Executable**: `SyncBackup_v1.5.zip`
- **Source Code**: `Source code (zip)` or `Source code (tar.gz)`

**Full Changelog**: https://github.com/zaja/SyncBackup/compare/v1.4...v1.5
