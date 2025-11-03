# SyncBackup v1.4 - Release Notes

**Release Date:** November 3, 2025  
**Author:** Goran Zajec  
**Website:** https://svejedobro.hr

## 🎉 What's New in v1.4

This release focuses on **fixing critical Windows Service issues** and improving service management capabilities.

### 🔧 Windows Service - Major Fixes

#### Fixed: ModuleNotFoundError
- **Problem**: Service failed to start with `ModuleNotFoundError: No module named 'app'`
- **Solution**: Implemented early `sys.path` configuration before all imports
- **Impact**: Service now starts reliably without module import errors

#### Fixed: Service Registration
- **Problem**: Service not visible in Windows Services Manager (services.msc)
- **Solution**: Added required service attributes (`_svc_reg_class_`, `_exe_name_`, `_exe_args_`)
- **Impact**: Service properly registers and appears in services.msc

#### Improved: Service Installation
- **Problem**: Unreliable service installation using `HandleCommandLine`
- **Solution**: Direct `InstallService` call with explicit parameters
- **Impact**: More reliable and predictable service installation

### 🛠️ New Tools & Documentation

#### service_manager.py - Command Line Helper
New helper script for easy service management:

```powershell
python service_manager.py install    # Install service
python service_manager.py start      # Start service
python service_manager.py stop       # Stop service
python service_manager.py restart    # Restart service
python service_manager.py status     # Check status
python service_manager.py uninstall  # Uninstall service
python service_manager.py debug      # Run in debug mode
```

#### Comprehensive Documentation
- **SERVIS_UPUTE.md** - Quick guide in Croatian
- **SERVICE_TROUBLESHOOTING.md** - Detailed troubleshooting in English
- **WINDOWS_SERVICE_FIX.md** - Quick fix overview
- **SUMMARY_OF_CHANGES.md** - Detailed change summary
- **QUICK_TEST.md** - 10-step quick test guide

### 📝 Enhanced Logging
- Service errors now logged to `app/service_error.log`
- Better error messages and stack traces
- Easier debugging and troubleshooting

### ✅ Improvements from v1.3

All features from v1.3 are included and improved:
- Settings Tab with centralized configuration
- Notification Batching (Immediate, Batch, Disabled modes)
- Windows Service Support (now fully functional)
- Language Selection (Croatian/English)
- Enhanced Database with settings and notification queue

## 🚀 Installation & Upgrade

### New Installation

```bash
# Clone repository
git clone https://github.com/yourusername/SyncBackup.git
cd SyncBackup

# Install dependencies
pip install -r app/requirements.txt

# Run application
python main.py
```

### Upgrading from v1.3

```bash
# Pull latest changes
git pull origin master

# No database migration needed - fully compatible with v1.3

# If you have Windows Service installed, reinstall it:
python service_manager.py uninstall
python service_manager.py install
```

## 🔧 Windows Service Setup

### Quick Setup (5 minutes)

1. **Uninstall old service** (if exists):
```powershell
sc stop SyncBackupService
sc delete SyncBackupService
```

2. **Install new service** (as Administrator):
```powershell
python service_manager.py install
```

3. **Verify installation**:
```powershell
python service_manager.py status
services.msc  # Look for "SyncBackup - Folder Sync & Backup Service"
```

4. **Test in debug mode**:
```powershell
python service_manager.py debug
# Press Ctrl+C to stop
```

5. **Start service**:
```powershell
python service_manager.py start
```

For detailed instructions, see `QUICK_TEST.md`.

## 📋 System Requirements

- **Operating System**: Windows 10/11, Linux, macOS
- **Python**: 3.7 or higher
- **Dependencies**: See `app/requirements.txt`
- **Windows Service**: Requires `pywin32` package and Administrator privileges

## 🐛 Bug Fixes

### Critical Fixes
- ✅ Fixed `ModuleNotFoundError: No module named 'app'` in Windows Service
- ✅ Fixed service not appearing in services.msc
- ✅ Fixed unreliable service installation

### Improvements
- ✅ Better error handling and logging
- ✅ Admin privilege checks
- ✅ Service auto-start configuration
- ✅ Enhanced service status reporting

## 📚 Documentation

### New Documentation Files
- `service_manager.py` - Service management helper
- `SERVIS_UPUTE.md` - Croatian quick guide
- `SERVICE_TROUBLESHOOTING.md` - English troubleshooting
- `WINDOWS_SERVICE_FIX.md` - Quick fix overview
- `SUMMARY_OF_CHANGES.md` - Detailed changes
- `QUICK_TEST.md` - Quick test guide

### Updated Documentation
- `README.md` - Added Windows Service section and troubleshooting
- `.gitignore` - Added service_error.log

## 🔍 Known Issues

None at this time. If you encounter any issues, please:
1. Check `SERVIS_UPUTE.md` or `SERVICE_TROUBLESHOOTING.md`
2. Review logs in `app/service.log` and `app/service_error.log`
3. Open an issue on GitHub

## 🙏 Acknowledgments

Special thanks to all users who reported the Windows Service issues and helped with testing.

## 📞 Support

- **GitHub Issues**: https://github.com/yourusername/SyncBackup/issues
- **Documentation**: See README.md and troubleshooting guides
- **Website**: https://svejedobro.hr

## 📝 Full Changelog

For a complete list of changes, see `CHANGES_v1.4.md`.

---

**Download:** [SyncBackup v1.4](https://github.com/yourusername/SyncBackup/releases/tag/v1.4)

**Previous Release:** [v1.3](https://github.com/yourusername/SyncBackup/releases/tag/v1.3)
