# SyncBackup v1.4 - Windows Service Fixes 🔧

## 🎯 What's Fixed

This release **fixes critical Windows Service issues** that prevented the service from starting and being visible in Windows Services Manager.

### Critical Fixes

✅ **Fixed ModuleNotFoundError** - Service now starts without `ModuleNotFoundError: No module named 'app'`  
✅ **Fixed Service Registration** - Service now properly appears in Windows Services Manager (services.msc)  
✅ **Improved Installation** - More reliable service installation process  
✅ **Enhanced Error Logging** - Errors now logged to `app/service_error.log` for easier debugging  

## 🛠️ New Features

### service_manager.py - Command Line Helper

Easy service management from PowerShell:

```powershell
python service_manager.py install    # Install service
python service_manager.py start      # Start service
python service_manager.py stop       # Stop service
python service_manager.py status     # Check status
python service_manager.py debug      # Run in debug mode
```

### Comprehensive Documentation

- **QUICK_TEST.md** - 10-step quick test guide
- **SERVIS_UPUTE.md** - Quick guide (Croatian)
- **SERVICE_TROUBLESHOOTING.md** - Detailed troubleshooting (English)
- **WINDOWS_SERVICE_FIX.md** - Quick fix overview
- **SUMMARY_OF_CHANGES.md** - Technical details

## 🚀 Quick Start

### For New Users

```bash
git clone https://github.com/zaja/SyncBackup.git
cd SyncBackup
pip install -r app/requirements.txt
python main.py
```

### For Existing Users (Upgrading from v1.3)

```bash
git pull origin main

# If you have Windows Service installed, reinstall it:
python service_manager.py uninstall
python service_manager.py install
```

## 🔧 Windows Service Setup

**Run PowerShell as Administrator:**

```powershell
# Remove old service (if exists)
sc delete SyncBackupService

# Install new service
python service_manager.py install

# Verify
python service_manager.py status
services.msc  # Look for "SyncBackup - Folder Sync & Backup Service"

# Start service
python service_manager.py start
```

See **QUICK_TEST.md** for detailed testing steps.

## 📋 What's Included from v1.3

All v1.3 features are included:
- ⚙️ Settings Tab with centralized configuration
- 🔔 Notification Batching (Immediate/Batch/Disabled modes)
- 🌐 Language Selection (Croatian/English)
- 📊 Dashboard with real-time statistics
- 🔄 Simple and Incremental backup jobs
- ⏰ Advanced scheduler
- 🗃️ SQLite database
- 🔽 System tray functionality

## 📝 Full Changelog

See **CHANGES_v1.4.md** for detailed technical changes.

## 🐛 Bug Fixes

- Fixed `ModuleNotFoundError: No module named 'app'` in Windows Service
- Fixed service not appearing in services.msc
- Fixed unreliable service installation
- Improved error handling and logging
- Added admin privilege checks

## 📚 Documentation

- **README.md** - Updated with Windows Service documentation
- **RELEASE_NOTES_v1.4.md** - Complete release notes
- **CHANGES_v1.4.md** - Detailed technical changes
- **QUICK_TEST.md** - Quick testing guide
- **SERVIS_UPUTE.md** - Croatian quick guide
- **SERVICE_TROUBLESHOOTING.md** - English troubleshooting guide

## 💾 Download

**Source Code:**
- [Source code (zip)](https://github.com/zaja/SyncBackup/archive/refs/tags/v1.4.zip)
- [Source code (tar.gz)](https://github.com/zaja/SyncBackup/archive/refs/tags/v1.4.tar.gz)

## 📞 Support

- **Issues:** https://github.com/zaja/SyncBackup/issues
- **Documentation:** See README.md and troubleshooting guides
- **Website:** https://svejedobro.hr

## 🙏 Acknowledgments

Thanks to all users who reported Windows Service issues and helped with testing!

---

**Previous Release:** [v1.3](https://github.com/zaja/SyncBackup/releases/tag/v1.3)
