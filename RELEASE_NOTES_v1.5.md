# 🎉 SyncBackup v1.5 - Release Notes

## Major Release - November 8, 2025

### 🌟 Highlights

This is a **major release** with significant improvements to the incremental backup system, introducing **true incremental backups**, **chain-based retention policy**, and **preserve deleted files** functionality.

---

## ✅ What's New

### 1. True Incremental Backup System
- **INICIAL backups**: Full baseline backups with `_INICIAL` suffix
- **Incremental backups**: Only changed/new files in separate folders
- **Smart comparison**: Uses modification time and file size
- **No more sync directory**: Each backup is independent

### 2. Reset Chain After N Incrementals
- Automatically creates new INICIAL backup after N incrementals
- Prevents long chains that are hard to restore
- Configurable: 0 = never reset, 30 = monthly reset
- Logged in activity: "Resetting backup chain after N incremental backups"

### 3. Preserve Deleted Files
- Deleted files marked with `_DELETED` suffix
- Easy recovery: remove suffix to restore
- Prevents accidental data loss
- Works seamlessly with incremental backups

### 4. Chain-Based Retention Policy
- **Incremental jobs**: Deletes entire chains (INICIAL + incrementals)
- **Simple jobs**: Deletes individual backup folders
- Simplified to "Keep N" only (removed days/size options)
- Automatic cleanup after each backup

### 5. Dashboard Improvements
- **Larger Recent Activity**: 15 lines vs 8
- **More details**: Date, time, status, duration, files count
- **Better format**: Columnar layout with separators
- **More history**: 30 entries vs 20

### 6. Windows Service Updates
- Full support for all new features
- Reset chain after N
- Preserve deleted files
- Retention policy with chains
- Improved logging

---

## 🔧 Technical Changes

### Database Schema
- Added `reset_chain_after` column
- Removed `create_snapshots` and `snapshot_interval`
- Support for `incremental_inicial` and `incremental` file types
- Migration script: `migrate_reset_chain_after.py`

### Logging
- Detailed logs for chain resets
- Deleted file tracking
- Retention policy actions
- All new features logged

### Code Quality
- Improved error handling
- Better edge case management
- Comprehensive test coverage
- Updated documentation

---

## 📋 Migration Guide

### For Existing Users:

1. **Backup your database**:
   ```bash
   copy app\sync_backup.db app\sync_backup.db.backup
   ```

2. **Run migration** (if upgrading from v1.4):
   ```bash
   python migrate_reset_chain_after.py
   ```

3. **Review job settings**:
   - Old snapshot settings migrated to `reset_chain_after`
   - Check and adjust as needed

4. **Test first**:
   - Test with non-critical jobs
   - Verify backups work as expected

### Breaking Changes:
- Snapshot feature removed (replaced with reset_chain_after)
- Retention policy simplified (only "Keep N" remains)
- Database schema changed (migration required)

---

## 🐛 Bug Fixes

- Fixed duplicate INICIAL backups
- Fixed database CHECK constraint errors
- Improved retention policy reliability
- Better handling of edge cases

---

## 📝 Files Changed

### Core Application:
- `main.py` - Version 1.5, new features
- `app/windows_service.py` - Full feature parity
- `app/database.py` - Schema updates

### Documentation:
- `README.md` - Updated for v1.5
- `CHANGELOG_v1.5.md` - Detailed changelog
- `MANUAL_EN.html` - Updated user manual

### Configuration:
- `.gitignore` - Excludes test files

---

## 🚀 What's Next

### Planned for v1.6:
- Cloud backup integration
- Email notifications
- Backup verification
- Compression improvements

---

## 🙏 Thank You!

Thank you to all users who provided feedback and helped test these new features!

**Author**: Goran Zajec  
**Website**: https://svejedobro.hr  
**GitHub**: https://github.com/zaja/SyncBackup

---

**Download**: [SyncBackup v1.5](https://github.com/zaja/SyncBackup/releases/tag/v1.5)
