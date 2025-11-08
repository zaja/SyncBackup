# SyncBackup v1.5 - Changelog

## 🎉 Major Release - November 8, 2025

### 🚀 New Features

#### 1. **True Incremental Backup System**
- **INICIAL Backup**: First backup creates a full copy with `_INICIAL` suffix
- **Incremental Backups**: Subsequent backups only store changed/new files
- **Smart Comparison**: Uses modification time and file size for change detection
- **Separate Folders**: Each backup in its own timestamped folder

#### 2. **Reset Chain After N Incrementals**
- Automatically create new INICIAL backup after N incremental backups
- Prevents long chains that are hard to restore
- Configurable per job (0 = never reset)
- Example: Reset after 30 incrementals for monthly full backups

#### 3. **Preserve Deleted Files**
- Deleted files are marked with `_DELETED` suffix instead of being removed
- Easy recovery: just remove the `_DELETED` suffix
- Prevents accidental data loss
- Works with incremental backups

#### 4. **Chain-Based Retention Policy**
- **For Incremental Jobs**: Deletes entire chains (INICIAL + all incrementals)
- **For Simple Jobs**: Deletes individual backup folders
- Simplified to "Keep N backups/chains" only
- Automatic cleanup after each backup

### 📊 Dashboard Improvements

#### Enhanced Recent Activity
- **Larger Display**: 15 lines instead of 8
- **More Details**: Date, time, status, duration, files processed
- **Better Format**: Columnar layout with separators
- **More History**: Shows 30 entries instead of 20

#### Tab Reordering
- Log Viewer moved to last position
- More logical workflow: Dashboard → Jobs → Backup Files → Settings → Log Viewer

### 🔧 Technical Improvements

#### Windows Service Updates
- Full support for reset_chain_after
- Full support for preserve_deleted
- Retention policy implementation
- Improved logging

#### Database Schema
- New `reset_chain_after` column in jobs table
- Migration from old `create_snapshots` and `snapshot_interval`
- Support for `incremental_inicial` and `incremental` file types
- Improved UPSERT logic to prevent duplicates

#### Logging Enhancements
- Detailed logs for all new features
- Chain reset notifications
- Deleted file tracking
- Retention policy actions

### 🐛 Bug Fixes

- Fixed duplicate INICIAL backups issue
- Fixed database CHECK constraint errors
- Improved error handling in retention policies
- Better handling of edge cases in incremental backups

### 📝 Documentation

- Updated user manual (MANUAL_EN.html)
- Comprehensive README updates
- New feature documentation
- Migration guides

### ⚙️ Breaking Changes

- **Snapshot feature removed**: Replaced with reset_chain_after
- **Retention policy simplified**: Only "Keep N" option remains
- **Database migration required**: Run migrate_reset_chain_after.py

### 🔄 Migration Guide

1. **Backup your database** before upgrading
2. Run `migrate_reset_chain_after.py` to update schema
3. Review and update job configurations
4. Test with non-critical jobs first

### 📋 System Requirements

- Windows 10/11
- Python 3.8+
- 100 MB free disk space
- Administrator privileges (for Windows Service)

### 🙏 Acknowledgments

Special thanks to all users who provided feedback and helped test the new features!

---

**Full Changelog**: https://github.com/yourusername/syncbackup/compare/v1.4...v1.5
