# SyncBackup v1.2 - Advanced Folder Synchronization and Backup Application

**Author:** Goran Zajec  
**Website:** https://svejedobro.hr

## 📋 Overview

SyncBackup v1.2 is an advanced Python Tkinter application for folder synchronization and backup with automatic scheduling capabilities, file retention policy, SQLite database, system tray functionality, and comprehensive dashboard monitoring.

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
- **Tab Interface**: Organized display (Dashboard, Jobs, Logs, Backup Files)

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
├── main.py              # Main application (console mode)
├── main.pyw             # Main application (GUI mode, no console)
├── app/
│   ├── database.py      # SQLite database manager
│   ├── tray_icon.py     # System tray functionality
│   ├── sync_backup.db   # SQLite database (created automatically)
│   ├── MANUAL.html      # User manual (Croatian)
│   ├── MANUAL_EN.html   # User manual (English)
│   └── requirements.txt # Dependencies
└── README.md           # This file
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
Shows notifications when job completes:
- **Success**: Green notification with file count
- **Error**: Red notification with error description
- **Skipped**: Yellow notification (no changes)

### File Retention Policy
Automatic deletion of old backups:
- **Keep Count**: Keep last N backups
- **Keep Days**: Keep backups for N days
- **Keep Size**: Keep up to N MB

## 🗃️ Database

The application uses SQLite database (`app/sync_backup.db`) for:
- Job configurations
- Hash values for change detection
- Execution logs
- Backup file tracking
- Retention policy rules

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

## 📝 Changelog

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