# Changelog

All notable changes to SyncBackup will be documented in this file.

## [1.5] - 2025-11-08

### 🎉 Major Release - True Incremental Backups

#### Added
- **True Incremental Backup System**
  - INICIAL backups: Full baseline with all files
  - Incremental backups: Only changed/new files in separate folders
  - Smart change detection using modification time and file size
  
- **Reset Chain After N Incrementals**
  - Automatically create new INICIAL backup after N incremental backups
  - Prevents long restore chains
  - Configurable per job (0 = never reset)

- **Preserve Deleted Files**
  - Deleted files marked with `_DELETED` suffix instead of removal
  - Easy recovery by removing suffix
  - Prevents accidental data loss

- **Chain-Based Retention Policy**
  - For Incremental jobs: Deletes entire chains (INICIAL + all incrementals)
  - For Simple jobs: Deletes individual backup folders
  - Simplified to "Keep N" only
  - Automatic cleanup after each backup

#### Improved
- **Dashboard Enhancements**
  - Larger Recent Activity window (15 lines vs 8)
  - More detailed information (date, time, status, duration, files count)
  - Better columnar format with separators
  - Shows 30 entries instead of 20

- **Tab Reordering**
  - Log Viewer moved to last position
  - Better workflow: Dashboard → Jobs → Backup Files → Settings → Log Viewer

- **Windows Service**
  - Full support for all new features
  - Reset chain after N
  - Preserve deleted files
  - Retention policy with chains
  - Improved logging

#### Changed
- Database schema updated with `reset_chain_after` column
- Removed `create_snapshots` and `snapshot_interval` (replaced with reset_chain_after)
- Retention policy simplified to "Keep N" only
- Support for new backup file types: `incremental_inicial` and `incremental`

#### Fixed
- Fixed duplicate INICIAL backups issue
- Fixed database CHECK constraint errors
- Improved retention policy reliability
- Better edge case handling

---

## [1.4] - 2025-11-02

### Added
- Windows Service support for background operation
- Service installation and management from GUI
- Improved notification system with batching

### Fixed
- Windows Service execution issues
- Notification timing improvements

---

## [1.3] - 2025-10-28

### Added
- Notification batching system
- Dashboard improvements
- Better error handling

---

## Earlier Versions

See individual release notes for versions prior to 1.3.

---

**Full Release Notes**: See [Releases](https://github.com/zaja/SyncBackup/releases) page for detailed information.
