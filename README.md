# SyncBackup v1.4 - Advanced Folder Synchronization and Backup Application

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/zaja/SyncBackup)](https://github.com/zaja/SyncBackup/releases/latest)
[![GitHub Release Date](https://img.shields.io/github/release-date/zaja/SyncBackup)](https://github.com/zaja/SyncBackup/releases/latest)
[![GitHub Downloads](https://img.shields.io/github/downloads/zaja/SyncBackup/total)](https://github.com/zaja/SyncBackup/releases)
[![GitHub Stars](https://img.shields.io/github/stars/zaja/SyncBackup)](https://github.com/zaja/SyncBackup/stargazers)

**Author:** Goran Zajec  
**Website:** https://svejedobro.hr

![SyncBackup](https://raw.githubusercontent.com/zaja/SyncBackup/refs/heads/master/app/SyncBackup.png)

## 📥 Download Latest Release

**[📦 Download SyncBackup v1.4](https://github.com/zaja/SyncBackup/releases/latest)** - Windows Service Fixes & Improvements

---

## 📋 Overview

SyncBackup v1.4 is an advanced Python Tkinter application for folder synchronization and backup with automatic scheduling capabilities, file retention policy, SQLite database, system tray functionality, comprehensive dashboard monitoring, and Windows Service support.

## ✨ Key Features

### 📊 Dashboard
- **Real-time Statistics**: Total jobs, active jobs, backup sizes, success rates
- **Next Backup Info**: Shows which job runs next and when
- **Recent Activity**: Last 24 hours of job executions with status indicators
- **Auto-refresh**: Updates every 30 seconds automatically

### 🔄 Job Types

#### **Simple Job**
- Creates a complete copy of the source folder with datetime suffix
- Each execution creates a new backup folder (e.g., `folder_20251002_090326`)
- **ZIP Compression**: Option to compress backups as ZIP files for space saving
- **File Exclusion**: Exclude specific files/folders using patterns (e.g., .git, node_modules)
- **Desktop Notifications**: Optional notifications when jobs complete

#### **Incremental Job**
Incremental jobs work with **two different concepts**:

1. **🔄 Sync Directory** (Working Copy):
   - Location: `destination/source_folder_name/`
   - Purpose: Maintains an up-to-date synchronized copy of the source folder
   - Behavior: Updated incrementally with each job execution
   - **Not displayed** in Backup Files tab (it's a sync, not a backup)

2. **📸 Snapshots** (Archive Copies):
   - Location: `destination/source_folder_name_INCREMENTAL_20251002_090326/`
   - Purpose: Preserves the state at specific points in time
   - Behavior: Created periodically based on the snapshot interval
   - **Displayed** in Backup Files tab (these are actual backup files)

**Options:**
- **Preserve deleted files**: Keep files in sync directory even if deleted from source
- **Create snapshots**: Enable/disable periodic snapshot creation
- **Snapshot interval**: How often to create snapshots (hours/days/weeks)
- **File Exclusion**: Exclude specific files/folders using patterns
- **Desktop Notifications**: Optional notifications when jobs complete

**Important:** Only snapshots appear in the Backup Files tab, not the sync directory. This is by design - the sync directory is a working copy, while snapshots are archive backups for recovery purposes.

### ⏰ Advanced Scheduler
- **Every X minutes**: Run every X minutes
- **Every X hours**: Run every X hours
- **Daily**: Daily run at specified time
- **Weekly**: Weekly run on specified day
- **Monthly**: Monthly run on specified day

### 🖥️ GUI Interface
- **Dashboard**: Statistics overview with job counts, backup sizes, success rates, and recent activity
- **Jobs List**: TreeView with columns (Name, Type, Source, Destination, Schedule, Status, Running, Last Run, Next Run)
- **Log Viewer**: Real-time log display with filter options
- **Backup Files**: View and manage backup files
- **Settings**: Configure application preferences, notifications, language, and Windows Service
- **Tab Interface**: Organized display (Dashboard, Jobs, Logs, Backup Files, Settings)

### 🔧 Control Buttons
- **New Job**: Create new job (always visible)
- **Edit Selected**: Edit selected job (Jobs tab only)
- **Delete Job**: Delete job (Jobs tab only)
- **Open Destination**: Open destination folder in file explorer (Jobs tab only)
- **Activate Job**: Activate job (green color, Jobs tab only)
- **Deactivate Job**: Deactivate job (red color, Jobs tab only)
- **Run Selected**: Run selected job (brown color, Jobs tab only)

**Note:** Job control buttons are only visible when the Jobs tab is active for better UI organization.

### 🔽 System Tray Functionality
- **Minimize to tray**: Application minimizes to system tray
- **Tray menu**: Show/Quit options
- **X button**: Shows quit dialog before closing
- **Background operation**: Application runs in background

### 🔒 Single Instance
- **File locking**: Ensures only one application instance runs
- **Cross-platform**: Works on Windows, Linux and macOS
- **Automatic cleanup**: Automatic lock file cleanup

## 🚀 Installation

### Prerequisites
```bash
pip install -r app/requirements.txt
```

### Running
```bash
# Option 1: GUI mode (no console window)
double-click main.pyw

# Option 2: Console mode (with debug output)
python main.py
```

## 📁 File Structure

```
SyncBackup/
├── main.py                      # Main application (console mode)
├── main.pyw                     # Main application (GUI mode, no console)
├── service_manager.py           # Windows Service management helper
├── SERVIS_UPUTE.md             # Service troubleshooting (Croatian)
├── SERVICE_TROUBLESHOOTING.md  # Service troubleshooting (English)
├── app/
│   ├── database.py              # SQLite database manager
│   ├── tray_icon.py             # System tray functionality
│   ├── windows_service.py       # Windows Service implementation
│   ├── language_manager.py      # Multi-language support
│   ├── sync_backup.db           # SQLite database (created automatically)
│   ├── service.log              # Service log (created when service runs)
│   ├── languages/
│   │   ├── en.json              # English translations
│   │   └── hr.json              # Croatian translations
│   └── requirements.txt         # Dependencies
└── README.md                   # This file
```

## ⚙️ Additional Features

### File Exclusion Patterns
Exclude specific files/folders from backup. Examples:
- `.git,node_modules,__pycache__`
- `*.tmp,*.log,Thumbs.db`
- `cache/*,temp/*`

### ZIP Compression
Available only for Simple jobs. Compresses backup as ZIP file for space saving.

### Desktop Notifications
Shows notifications when job completes with three modes:
- **Immediate Mode**: Show notification for each backup job as it completes
- **Batch Mode** (Default): Group multiple notifications and show a summary every 5 minutes
  - Prevents notification spam when many backups run while user is away
  - Shows consolidated summary: "✅ 5 completed, ❌ 1 failed, ⏸️ 2 skipped"
- **Disabled**: No notifications

Notification types:
- **Success**: Green notification with file count
- **Error**: Red notification with error description
- **Skipped**: Yellow notification (no changes)

### File Retention Policy
Automatic deletion of old backups:
- **Keep Count**: Keep last N backups
- **Keep Days**: Keep backups for N days
- **Keep Size**: Keep up to N MB

### ⚙️ Settings Tab
Centralized configuration for application preferences:
- **Language Selection**: Choose between Croatian (Hrvatski) and English
- **Notification Settings**: 
  - Select notification mode (Immediate, Batch, or Disabled)
  - Configure batch notification interval (60-3600 seconds)
- **Windows Service** (Windows only):
  - Install/uninstall application as Windows Service
  - Run backups in background without user login
  - Auto-start with Windows
  - Requires administrator privileges

### 🔧 Windows Service Support
Run SyncBackup as a Windows Service for unattended operation:
- **Background Operation**: Runs without user login
- **Auto-Start**: Starts automatically with Windows
- **Service Management**: Install, uninstall, and check status from Settings tab or command line
- **Requirements**: 
  - Windows operating system
  - Administrator privileges
  - pywin32 package (install with: `pip install pywin32`)

#### Command Line Service Management
Use the `service_manager.py` helper script for easy service management:

```powershell
# Run PowerShell as Administrator, then:

# Install service
python service_manager.py install

# Start service
python service_manager.py start

# Check status
python service_manager.py status

# Stop service
python service_manager.py stop

# Uninstall service
python service_manager.py uninstall

# Debug mode (run in console)
python service_manager.py debug
```

**Important:** Service must be installed and managed with Administrator privileges.

For detailed troubleshooting, see `SERVIS_UPUTE.md` (Croatian) or `SERVICE_TROUBLESHOOTING.md` (English).

## 🗃️ Database

The application uses SQLite database (`app/sync_backup.db`) for:
- Job configurations
- Hash values for change detection
- Execution logs
- Backup file tracking
- Retention policy rules
- Application settings
- Notification queue (for batch mode)

## 🛠️ Troubleshooting

### Job Not Running
- Check if job is active
- Check "Next Run" column
- Look at logs for errors

### Empty Backup
- Check if source folder exists
- Check read/write permissions
- Check exclude patterns

### Application Won't Start
- Check if all modules are installed
- Run from command prompt to see errors
- Check Python version (3.7+)

### Windows Service Issues

#### Service not visible in services.msc
1. Remove old service: `sc delete SyncBackupService`
2. Reinstall: `python service_manager.py install`
3. Check: `python service_manager.py status`

#### ModuleNotFoundError: No module named 'app'
- This should be fixed in the latest version
- If still occurs, check `app\service_error.log`
- Try debug mode: `python service_manager.py debug`

#### Service won't start
1. Check logs: `type app\service.log`
2. Check error log: `type app\service_error.log`
3. Run in debug mode: `python service_manager.py debug`
4. Verify admin privileges

#### Access Denied errors
- Run PowerShell as Administrator
- Right-click → "Run as Administrator"

For detailed service troubleshooting, see:
- `SERVIS_UPUTE.md` (Croatian)
- `SERVICE_TROUBLESHOOTING.md` (English)

## 📝 Changelog

### v1.4 (2025-11-03)
- **Settings Tab**: New centralized settings interface
- **Notification Batching**: Smart notification grouping to prevent spam
  - Three modes: Immediate, Batch (default), and Disabled
  - Configurable batch interval (1-60 minutes)
  - Summary notifications show aggregated results
- **Windows Service Support**: Run as Windows Service (optional)
  - Background operation without user login
  - Auto-start with Windows
  - Service management from Settings tab and command line
  - **Fixed**: Module import errors (ModuleNotFoundError: No module named 'app')
  - **Fixed**: Service registration issues (service not visible in services.msc)
  - **Added**: `service_manager.py` helper script for easy command-line management
  - **Added**: Comprehensive troubleshooting guides (SERVIS_UPUTE.md, SERVICE_TROUBLESHOOTING.md)
- **Language Selection**: Choose between Croatian and English (UI labels to be translated)
- **Enhanced Database**: New tables for settings and notification queue
- **Improved User Experience**: Prevents notification overload when multiple backups complete

### v1.2 (2025-10-02)
- **Dashboard Tab**: New comprehensive statistics and monitoring interface
- **Real-time Statistics**: Job counts, backup sizes, success rates
- **Activity Monitoring**: Recent 24h activity with status indicators
- **Auto-refresh**: Dashboard updates every 30 seconds automatically
- **Next Backup Info**: Shows upcoming scheduled jobs with countdown
- **Open Destination**: Quick access to destination folders from Jobs tab
- **File Exclusion Patterns**: Exclude files/folders during backup (e.g., .git, node_modules, __pycache__)
- **Desktop Notifications**: Optional notifications for job completion, errors, and skipped jobs
- **ZIP Compression**: Compress Simple job backups as ZIP files for space saving
- **Conditional UI**: Job control buttons only visible on Jobs tab for cleaner interface
- **Enhanced Job Dialog**: Improved dialog size and layout for all new options

### v1.1 (2025-10-02)
- **Database Migration**: Migrated from JSON to SQLite database
- **Enhanced Logging**: Database-based logging system with filtering
- **System Tray**: Minimize to system tray functionality
- **Single Instance**: Prevent multiple application instances
- **File Structure**: Reorganized files into app/ directory
- **Multi-selection**: Select and manage multiple jobs/backups
- **Missing Files Detection**: Visual indicators for missing backup files
- **Executable Version**: PyInstaller-based .exe distribution

## 📄 License

MIT License

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📞 Support

For problems or questions, open an issue on GitHub or contact the developer.

---

**Author:** Goran Zajec  
**Website:** https://svejedobro.hr