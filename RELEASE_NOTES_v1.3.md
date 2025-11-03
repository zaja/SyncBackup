# SyncBackup v1.3 Release Notes

## 🎉 What's New in v1.3

### 🔔 Smart Notification Batching
**Problem Solved:** No more notification spam! When multiple backups complete while you're away, you won't see 20+ notifications popping up one after another.

**Solution:**
- **Batch Mode** (Default): Groups notifications and shows a summary every 5 minutes
  - Example: "📊 Backup Summary (15 jobs): ✅ 12 completed, ❌ 2 failed, ⏸️ 1 skipped"
- **Immediate Mode**: Shows notifications instantly (old behavior)
- **Disabled Mode**: No notifications at all

### 🔧 Windows Service Support
Run SyncBackup as a Windows Service for unattended operation!

**Features:**
- Background operation without user login
- Auto-start with Windows
- Perfect for servers and NAS devices
- Install/Uninstall/Status management from GUI

**Requirements:**
- Windows OS
- Administrator privileges
- pywin32 package (optional): `pip install pywin32`

### ⚙️ Settings Tab
New centralized settings interface for easy configuration!

**Sections:**
1. **Language Selection**: Choose between Croatian (Hrvatski) and English
2. **Notification Settings**: 
   - Select notification mode (Immediate/Batch/Disabled)
   - Configure batch interval (60-3600 seconds)
3. **Windows Service Settings**: 
   - Install/Uninstall service
   - Check service status
   - Enable/Disable service mode

## 📦 Installation

### Standard Installation
```bash
# Clone the repository
git clone https://github.com/zaja/SyncBackup.git
cd SyncBackup

# Install dependencies
pip install -r app/requirements.txt

# Run the application
python main.py
```

### With Windows Service Support
```bash
# Install additional dependency
pip install pywin32

# Run as administrator to install service
python main.py
# Then go to Settings tab → Install Service
```

## 🚀 Quick Start

1. **Launch the application:**
   ```bash
   python main.py
   ```

2. **Configure notifications:**
   - Go to **Settings** tab
   - Choose your notification mode
   - Click **Save Settings**

3. **Optional - Install as Windows Service:**
   - Run as Administrator
   - Go to **Settings** tab
   - Click **Install Service**
   - Start the service from Windows Services

## 📊 Technical Details

### New Database Tables
- `app_settings`: Application settings storage
- `notification_queue`: Notification batching queue

### New Files
- `app/windows_service.py`: Windows Service implementation
- `CHANGES_v1.3.md`: Detailed changelog
- `QUICK_START_v1.3.md`: Quick start guide
- `test_v1.3_features.py`: Feature test script

### Modified Files
- `main.py`: Added Settings tab and notification batching
- `app/database.py`: New tables and methods
- `app/requirements.txt`: Added pywin32 as optional dependency
- `README.md`: Updated documentation

## 🧪 Testing

Run the test script to verify all new features:
```bash
python test_v1.3_features.py
```

## 📝 Full Changelog

### Added
- ✅ Notification batching system with three modes
- ✅ Windows Service support (optional)
- ✅ Settings tab with centralized configuration
- ✅ Language selection (Croatian/English)
- ✅ Configurable batch notification interval
- ✅ Service install/uninstall/status management
- ✅ New database tables for settings and notification queue
- ✅ Notification processor thread for batch mode
- ✅ Automatic cleanup of old notifications

### Changed
- 🔄 Updated notification system to support batching
- 🔄 Enhanced database schema with new tables
- 🔄 Improved user experience with Settings tab
- 🔄 Version bumped to 1.3

### Fixed
- 🐛 Notification spam when multiple backups complete
- 🐛 No centralized settings management

## 🔗 Links

- **Repository:** https://github.com/zaja/SyncBackup
- **Documentation:** [README.md](README.md)
- **Detailed Changes:** [CHANGES_v1.3.md](CHANGES_v1.3.md)
- **Quick Start:** [QUICK_START_v1.3.md](QUICK_START_v1.3.md)
- **Website:** https://svejedobro.hr

## 👤 Author

**Goran Zajec**
- Website: https://svejedobro.hr
- GitHub: [@zaja](https://github.com/zaja)

## 📄 License

This project is open source and available for personal and commercial use.

## 🙏 Acknowledgments

Thanks to all users who provided feedback and feature requests!

---

**Version:** 1.3  
**Release Date:** November 3, 2025  
**Status:** ✅ Stable
