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
- All backup folders are displayed in the Backup Files tab
- Checks for changes before copying to avoid unnecessary backups
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
- **File Exclusion**: Exclude specific files/folders using patterns (e.g., .git, node_modules)
- **Desktop Notifications**: Optional notifications when jobs complete

**Important:** Only snapshots appear in the Backup Files tab, not the sync directory. This is by design - the sync directory is a working copy, while snapshots are archive backups for recovery purposes.

### ⏰ Advanced Scheduler
- **Every X minutes**: Run every X minutes
- **Every X hours**: Run every X hours
- **Daily**: Daily run at specified time
- **Weekly**: Weekly run on specified day
- **Monthly**: Monthly run on specified day

### 🗄️ SQLite Database
- **Jobs**: Job configurations
- **Backup Hashes**: Hash values for change detection
- **Job Logs**: Job execution logs
- **Retention Policies**: File retention policies
- **Backup Files**: Backup file tracking

### 🗂️ File Retention Policy
- **Keep Count**: Keep last X backups
- **Keep Days**: Keep backups older than X days
- **Keep Size**: Keep backups up to specified size (MB)

### 🖥️ GUI Interface
- **Dashboard**: Statistics overview with job counts, backup sizes, success rates, and recent activity
- **Jobs List**: TreeView with columns (Name, Type, Source, Destination, Schedule, Status, Running, Last Run, Next Run)
- **Log Viewer**: Real-time log display with filter options
- **Backup Files**: View and manage backup files
- **Tab Interface**: Organized display (Dashboard, Jobs, Logs, Backup Files)

### 🎨 Advanced Styling
- **Dynamic colors**: Active jobs (light green), inactive (light yellow)
- **Custom tabs**: Blue header with white text, bold font
- **Icons**: Relevant icons for all buttons
- **Responsive layout**: Adjustable sizes and padding

### 🔧 Control Buttons
- **New Job**: Create new job (always visible)
- **Edit Selected**: Edit selected job (Jobs tab only)
- **Delete Job**: Delete job (Jobs tab only)
- **Open Destination**: Open destination folder in file explorer (Jobs tab only)
- **Activate Job**: Activate job (green color, Jobs tab only)
- **Deactivate Job**: Deactivate job (red color, Jobs tab only)
- **Run Selected**: Run selected job (brown color, Jobs tab only)

**Note:** Job control buttons are only visible when the Jobs tab is active for better UI organization.

### 📊 Logging System
- **Database logging**: All logs stored in SQLite database
- **Real-time display**: Automatic log viewer refresh
- **Filter options**: Filter by job and status
- **Export**: Save logs to file
- **Clear logs**: Delete all logs from database

### 🖱️ System Tray Functionality
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
pip install tkinter
pip install schedule
pip install pystray
pip install pillow
```

### Running
```bash
python main.py
```

## 📁 File Structure

```
synhroapp/
├── main.py              # Main application
├── app/
│   ├── database.py      # SQLite database
│   ├── tray_icon.py     # System tray functionality
│   ├── sync_backup.db   # SQLite database (created automatically)
│   ├── README.md        # Documentation
│   ├── MANUAL.html      # User manual (Croatian)
│   ├── MANUAL_EN.html   # User manual (English)
│   └── requirements.txt # Dependencies
└── main.pyw            # Windows launcher (no console)
```

## 🗃️ Database

### Tables
- **jobs**: Job configurations
- **backup_hashes**: Hash values for change detection
- **job_logs**: Execution logs
- **retention_policies**: Retention policies
- **backup_files**: Backup file tracking

### Migration
The application automatically migrates existing JSON files to SQLite database on first run.

## ⚙️ Configuration

### Job Configuration
- **Name**: Unique job name
- **Type**: Simple or Incremental
- **Source/Destination**: Folder paths
- **Active**: Enables automatic execution
- **Schedule**: Schedule configuration
- **Retention Policy**: File retention policy

### Incremental Options
- **Preserve deleted files**: Keep deleted files
- **Create snapshots**: Create periodic snapshots
- **Snapshot interval**: Interval for snapshots (minutes/hours/days/weeks)

## 🔄 Working with the Application

### Creating a Job
1. Click "New Job"
2. Enter name and select type
3. Choose source and destination folders
4. Configure schedule
5. Set retention policy (optional)
6. Click "Save"

### Running a Job
- **Automatic**: According to configured schedule
- **Manual**: Click "Run Selected"
- **Force run**: Run without change detection

### Managing Jobs
- **Activate/Deactivate**: Enable/disable automatic execution
- **Edit**: Edit configuration
- **Delete**: Delete job

## 📊 Monitoring

### Log Viewer
- Real-time log display
- Filter by job and status
- Export to file
- Clear logs option

### Backup Files
- View all backup files
- Filter by job and type
- Delete selected backups
- Size and date information

## 🛠️ Troubleshooting

### Common Issues
1. **Job not running**: Check if job is active
2. **No changes**: Check source folder
3. **Database error**: Check SQLite database
4. **Tray icon not working**: Install pystray and pillow

### Logs
All logs are stored in SQLite database and can be viewed in Log Viewer tab.

## 🔧 Development

### Adding New Features
1. Modify `main.py` for GUI
2. Update `database.py` for database
3. Test with existing jobs

### Database
- Use `DatabaseManager` class for all DB operations
- Add new tables in `_create_tables` method
- Implement CRUD operations

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

### v1.0.7
- Basic functionality
- Simple and Incremental jobs
- Scheduler
- JSON storage

### v1.0.8
- SQLite database
- File retention policy
- Backup files tracking
- Database logging

### v1.0.9
- System tray functionality
- Single instance enforcement
- Advanced GUI styling
- Icons and UX improvements

### v1.1
- Added version to window title
- Updated documentation
- Stability improvements
- Author information added

## 📄 License

MIT License

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📞 Support

For problems or questions, open an issue on GitHub or contact the developer.