# SyncBackup v1.4 - Detailed Changes

**Release Date:** November 3, 2025  
**Focus:** Windows Service Fixes and Improvements

## 🔧 Windows Service - Critical Fixes

### 1. Fixed ModuleNotFoundError

**Problem:**
```
Error 0xC0000004 - Python could not import the service's module
ModuleNotFoundError: No module named 'app'
```

**Root Cause:**
When Windows Service Manager starts a Python script, it runs in a different execution context where `sys.path` doesn't include the parent directory. The `app` module couldn't be found.

**Solution:**
```python
# BEFORE (windows_service.py, line 15)
sys.path.insert(0, str(Path(__file__).parent.parent))

# AFTER (windows_service.py, lines 14-19)
# CRITICAL: Add parent directory to path BEFORE any other imports
_service_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_service_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)
```

**Files Changed:**
- `app/windows_service.py` (lines 14-19)

### 2. Fixed Service Registration

**Problem:**
Service installed successfully but was not visible in Windows Services Manager (services.msc).

**Root Cause:**
Missing required service attributes that Windows Service Manager uses for proper registration.

**Solution:**
Added missing attributes to `SyncBackupService` class:

```python
# ADDED (windows_service.py)
_svc_reg_class_ = "PythonService"
_exe_name_ = sys.executable
_exe_args_ = f'"{os.path.abspath(__file__)}"'
```

**Files Changed:**
- `app/windows_service.py` (lines 39-41)

### 3. Improved Service Installation

**Problem:**
Using `HandleCommandLine` for installation was not reliable and didn't provide enough control.

**Solution:**
Replaced with direct `InstallService` call with explicit parameters:

```python
# BEFORE
sys.argv = ['', 'install']
win32serviceutil.HandleCommandLine(ServiceClass)

# AFTER
win32serviceutil.InstallService(
    ServiceClass._svc_reg_class_,
    ServiceClass._svc_name_,
    ServiceClass._svc_display_name_,
    description=ServiceClass._svc_description_,
    exeName=sys.executable,
    exeArgs=f'"{service_script}"'
)

# Set service to auto-start
hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
hs = win32service.OpenService(hscm, ServiceClass._svc_name_, win32service.SERVICE_ALL_ACCESS)
win32service.ChangeServiceConfig(
    hs, win32service.SERVICE_NO_CHANGE,
    win32service.SERVICE_AUTO_START,
    win32service.SERVICE_NO_CHANGE,
    None, None, 0, None, None, None,
    ServiceClass._svc_display_name_
)
```

**Files Changed:**
- `app/windows_service.py` - `install_service()` function (lines 158-218)

### 4. Enhanced Error Logging

**Problem:**
Service startup errors were not logged, making debugging difficult.

**Solution:**
Added error logging to file:

```python
except Exception as e:
    # Log error to file for debugging
    from datetime import datetime
    log_path = Path(service_dir) / "service_error.log"
    with open(log_path, 'a') as f:
        f.write(f"\n{datetime.now()}: Service start error: {e}\n")
        import traceback
        traceback.print_exc(file=f)
    raise
```

**Files Changed:**
- `app/windows_service.py` - `__main__` block (lines 338-345)

### 5. Improved Service Uninstallation

**Problem:**
Service uninstallation didn't check for admin privileges or stop running service first.

**Solution:**
Added admin check and service stop before uninstall:

```python
# Ensure we're running as administrator
import ctypes
if not ctypes.windll.shell32.IsUserAnAdmin():
    print("Error: Administrator privileges required to uninstall service")
    return False

# Stop service first if running
try:
    win32serviceutil.StopService(ServiceClass._svc_name_)
    print("Stopping service...")
    time.sleep(2)
except:
    pass  # Service might not be running
```

**Files Changed:**
- `app/windows_service.py` - `uninstall_service()` function (lines 220-252)

## 🛠️ New Files

### 1. service_manager.py
**Purpose:** Command-line helper script for easy service management.

**Features:**
- Install service
- Uninstall service
- Start/Stop/Restart service
- Check service status
- Run service in debug mode (console)
- Admin privilege checks
- Detailed output and error messages

**Usage:**
```powershell
python service_manager.py install
python service_manager.py start
python service_manager.py status
python service_manager.py debug
```

### 2. SERVIS_UPUTE.md
**Purpose:** Quick setup and troubleshooting guide in Croatian.

**Contents:**
- Installation steps
- Quick commands
- Troubleshooting common issues
- GUI testing instructions

### 3. SERVICE_TROUBLESHOOTING.md
**Purpose:** Comprehensive troubleshooting guide in English.

**Contents:**
- Problem analysis
- Step-by-step testing procedures
- Common errors and solutions
- Debug information collection
- Windows Event Log checking

### 4. WINDOWS_SERVICE_FIX.md
**Purpose:** Quick overview of problems and solutions.

**Contents:**
- Problem description
- Root cause analysis
- Quick fix steps
- Expected results

### 5. SUMMARY_OF_CHANGES.md
**Purpose:** Detailed technical summary of all changes.

**Contents:**
- Root cause analysis
- Code changes with before/after comparisons
- New files description
- Testing procedures
- Technical details

### 6. QUICK_TEST.md
**Purpose:** 10-step quick test guide.

**Contents:**
- Step-by-step testing procedure
- Expected outputs
- Troubleshooting tips
- All commands reference

## 📝 Updated Files

### README.md
**Changes:**
- Updated version from v1.2 to v1.4 in title and overview
- Added Windows Service Command Line Management section
- Updated File Structure with new files
- Added Windows Service Issues to Troubleshooting section
- Updated Changelog with v1.4 fixes

**Lines Changed:** Multiple sections

### .gitignore
**Changes:**
- Added `app/service_error.log` to ignore list

**Lines Changed:** Line 43

### main.py
**Changes:**
- Updated version from v1.3 to v1.4 in docstring
- Updated app_name in notifications from "SyncBackup v1.3" to "SyncBackup v1.4"

**Lines Changed:** 
- Line 3: Version in docstring
- Line 2212: Notification app_name

### app/languages/hr.json
**Changes:**
- Updated window_title from "SyncBackup v1.3" to "SyncBackup v1.4"

**Lines Changed:** Line 5

### app/languages/en.json
**Changes:**
- Updated window_title from "SyncBackup v1.3" to "SyncBackup v1.4"

**Lines Changed:** Line 5

## 🔍 Technical Details

### Modified Functions in app/windows_service.py

1. **install_service()** - Completely rewritten
   - Added admin privilege check
   - Direct InstallService call
   - Auto-start configuration
   - Better output messages

2. **uninstall_service()** - Enhanced
   - Added admin privilege check
   - Stop service before uninstall
   - Better error handling

3. **__main__ block** - Improved
   - Error logging to file
   - Better exception handling

### Added Attributes in SyncBackupService

1. `_svc_reg_class_ = "PythonService"`
2. `_exe_name_ = sys.executable`
3. `_exe_args_ = f'"{os.path.abspath(__file__)}"'`

### Added Imports

1. `win32api` - For additional Windows API functions

## 🧪 Testing

### Test Scenarios Covered

1. ✅ Service installation
2. ✅ Service visibility in services.msc
3. ✅ Service start/stop
4. ✅ Debug mode execution
5. ✅ Error logging
6. ✅ Module import resolution
7. ✅ Admin privilege checks
8. ✅ Service uninstallation

### Test Files Created

- `QUICK_TEST.md` - 10-step test procedure
- `service_manager.py` - Testing tool

## 📊 Impact Analysis

### Before v1.4
- ❌ Service failed to start with ModuleNotFoundError
- ❌ Service not visible in services.msc
- ❌ Unreliable installation
- ❌ Poor error reporting

### After v1.4
- ✅ Service starts reliably
- ✅ Service visible and manageable in services.msc
- ✅ Consistent installation process
- ✅ Comprehensive error logging
- ✅ Easy command-line management
- ✅ Detailed documentation

## 🔄 Compatibility

### Backward Compatibility
- ✅ Fully compatible with v1.3 database
- ✅ No migration required
- ✅ All v1.3 features preserved

### Breaking Changes
- None

### Upgrade Path
1. Pull latest code
2. Uninstall old service (if installed)
3. Install new service
4. No database changes needed

## 📈 Statistics

- **Files Modified:** 6
- **Files Added:** 6
- **Lines Changed:** ~500
- **Functions Rewritten:** 2
- **New Documentation Pages:** 6

## 🎯 Future Improvements

Potential enhancements for future versions:
- GUI service installer wizard
- Service configuration file
- Multiple service instances support
- Service performance monitoring
- Automatic service recovery

---

**For complete release notes, see:** `RELEASE_NOTES_v1.4.md`
