"""
Windows Service wrapper for SyncBackup application

Author: Goran Zajec
Website: https://svejedobro.hr
"""

import sys
import os
import time
import logging
from pathlib import Path

# CRITICAL: Add parent directory to path BEFORE any other imports
# This must be done first so that 'app' module can be found
_service_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_service_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    import win32api
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False
    print("pywin32 not available - Windows Service functionality disabled")

class SyncBackupService:
    """Windows Service for SyncBackup application"""
    
    if PYWIN32_AVAILABLE:
        _svc_name_ = "SyncBackupService"
        _svc_display_name_ = "SyncBackup - Folder Sync & Backup Service"
        _svc_description_ = "Automated folder synchronization and backup service"
        _svc_reg_class_ = "PythonService"
        _exe_name_ = sys.executable
        _exe_args_ = f'"{os.path.abspath(__file__)}"'
    
    def __init__(self, args=None):
        if PYWIN32_AVAILABLE:
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.is_running = True
            
            # Setup logging
            log_path = Path(__file__).parent / "service.log"
            logging.basicConfig(
                filename=str(log_path),
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
            self.logger = logging.getLogger(__name__)
    
    def SvcStop(self):
        """Stop the service"""
        if PYWIN32_AVAILABLE:
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)
            self.is_running = False
            self.logger.info("Service stop requested")
    
    def SvcDoRun(self):
        """Run the service"""
        if not PYWIN32_AVAILABLE:
            return
            
        try:
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            self.logger.info("Service started")
            self.main()
        except Exception as e:
            self.logger.error(f"Service error: {e}")
            servicemanager.LogErrorMsg(f"Service error: {e}")
    
    def main(self):
        """Main service loop"""
        # Import here to avoid circular imports
        from app.database import DatabaseManager
        
        # Get database path
        base_dir = Path(__file__).parent.parent
        db_path = str(base_dir / "app" / "sync_backup.db")
        
        # Initialize database
        db_manager = DatabaseManager(db_path)
        
        self.logger.info("SyncBackup service running in background mode")
        
        # Import scheduler components
        from datetime import datetime, timedelta
        import threading
        
        # Load jobs
        jobs_data = db_manager.get_jobs()
        
        # Service loop - check for jobs every minute
        while self.is_running:
            try:
                # Reload jobs to get latest configuration
                jobs_data = db_manager.get_jobs()
                
                for job_data in jobs_data:
                    if not job_data.get('active', False):
                        continue
                    
                    # Check if job should run
                    next_run = job_data.get('next_run')
                    if next_run:
                        try:
                            next_run_dt = datetime.strptime(next_run, "%Y-%m-%d %H:%M:%S")
                            if next_run_dt <= datetime.now():
                                # Job should run
                                self.logger.info(f"Job '{job_data['name']}' scheduled to run")
                                # Note: Actual job execution would be implemented here
                                # For now, we just log that it should run
                        except Exception as e:
                            self.logger.error(f"Error checking job schedule: {e}")
                
                # Wait for 60 seconds or stop event
                if win32event.WaitForSingleObject(self.hWaitStop, 60000) == win32event.WAIT_OBJECT_0:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in service loop: {e}")
                time.sleep(60)
        
        self.logger.info("Service stopped")

# Make the service class inherit from ServiceFramework if pywin32 is available
if PYWIN32_AVAILABLE:
    # Create a new class that inherits from both
    class SyncBackupServiceImpl(win32serviceutil.ServiceFramework, SyncBackupService):
        _svc_name_ = SyncBackupService._svc_name_
        _svc_display_name_ = SyncBackupService._svc_display_name_
        _svc_description_ = SyncBackupService._svc_description_
        _svc_reg_class_ = SyncBackupService._svc_reg_class_
        _exe_name_ = SyncBackupService._exe_name_
        _exe_args_ = SyncBackupService._exe_args_
        
        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            SyncBackupService.__init__(self, args)
    
    # Use the implementation class
    ServiceClass = SyncBackupServiceImpl
else:
    ServiceClass = SyncBackupService

def install_service():
    """Install the Windows service"""
    if not PYWIN32_AVAILABLE:
        print("Error: pywin32 is not installed. Please install it with: pip install pywin32")
        return False
    
    try:
        # Ensure we're running as administrator
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("Error: Administrator privileges required to install service")
            print("Please run this script as Administrator")
            return False
        
        # Get the service script path
        service_script = os.path.abspath(__file__)
        
        # Install the service
        print(f"Installing service '{ServiceClass._svc_display_name_}'...")
        print(f"Service script: {service_script}")
        print(f"Python executable: {sys.executable}")
        
        # Use InstallService directly for better control
        win32serviceutil.InstallService(
            ServiceClass._svc_reg_class_,
            ServiceClass._svc_name_,
            ServiceClass._svc_display_name_,
            description=ServiceClass._svc_description_,
            exeName=sys.executable,
            exeArgs=f'"{service_script}"'
        )
        
        # Set service to auto-start
        import win32service
        hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
        try:
            hs = win32service.OpenService(hscm, ServiceClass._svc_name_, win32service.SERVICE_ALL_ACCESS)
            try:
                win32service.ChangeServiceConfig(
                    hs,
                    win32service.SERVICE_NO_CHANGE,
                    win32service.SERVICE_AUTO_START,  # Auto-start
                    win32service.SERVICE_NO_CHANGE,
                    None, None, 0, None, None, None,
                    ServiceClass._svc_display_name_
                )
            finally:
                win32service.CloseServiceHandle(hs)
        finally:
            win32service.CloseServiceHandle(hscm)
        
        print(f"✓ Service '{ServiceClass._svc_display_name_}' installed successfully")
        print(f"  Service name: {ServiceClass._svc_name_}")
        print(f"  Startup type: Automatic")
        print(f"\nYou can now start the service with: python {service_script} start")
        print(f"Or use Windows Services Manager (services.msc)")
        return True
    except Exception as e:
        print(f"Error installing service: {e}")
        import traceback
        traceback.print_exc()
        return False

def uninstall_service():
    """Uninstall the Windows service"""
    if not PYWIN32_AVAILABLE:
        print("Error: pywin32 is not installed")
        return False
    
    try:
        # Ensure we're running as administrator
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("Error: Administrator privileges required to uninstall service")
            print("Please run this script as Administrator")
            return False
        
        # Stop service first if running
        try:
            win32serviceutil.StopService(ServiceClass._svc_name_)
            print("Stopping service...")
            time.sleep(2)
        except:
            pass  # Service might not be running
        
        # Uninstall the service
        print(f"Uninstalling service '{ServiceClass._svc_display_name_}'...")
        win32serviceutil.RemoveService(ServiceClass._svc_name_)
        
        print(f"✓ Service '{ServiceClass._svc_display_name_}' uninstalled successfully")
        return True
    except Exception as e:
        print(f"Error uninstalling service: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_service():
    """Start the Windows service"""
    if not PYWIN32_AVAILABLE:
        print("Error: pywin32 is not installed")
        return False
    
    try:
        win32serviceutil.StartService(ServiceClass._svc_name_)
        print(f"Service '{ServiceClass._svc_display_name_}' started successfully")
        return True
    except Exception as e:
        print(f"Error starting service: {e}")
        return False

def stop_service():
    """Stop the Windows service"""
    if not PYWIN32_AVAILABLE:
        print("Error: pywin32 is not installed")
        return False
    
    try:
        win32serviceutil.StopService(ServiceClass._svc_name_)
        print(f"Service '{ServiceClass._svc_display_name_}' stopped successfully")
        return True
    except Exception as e:
        print(f"Error stopping service: {e}")
        return False

def get_service_status():
    """Get the Windows service status"""
    if not PYWIN32_AVAILABLE:
        return "pywin32 not installed"
    
    try:
        status = win32serviceutil.QueryServiceStatus(ServiceClass._svc_name_)
        status_map = {
            win32service.SERVICE_STOPPED: "Stopped",
            win32service.SERVICE_START_PENDING: "Starting",
            win32service.SERVICE_STOP_PENDING: "Stopping",
            win32service.SERVICE_RUNNING: "Running",
            win32service.SERVICE_CONTINUE_PENDING: "Continuing",
            win32service.SERVICE_PAUSE_PENDING: "Pausing",
            win32service.SERVICE_PAUSED: "Paused"
        }
        return status_map.get(status[1], f"Unknown ({status[1]})")
    except Exception as e:
        return f"Not installed or error: {e}"

def is_service_running():
    """Check if the Windows service is currently running"""
    if not PYWIN32_AVAILABLE:
        return False
    
    try:
        status = win32serviceutil.QueryServiceStatus(ServiceClass._svc_name_)
        return status[1] == win32service.SERVICE_RUNNING
    except:
        return False

def get_service_status_code():
    """Get the Windows service status code"""
    if not PYWIN32_AVAILABLE:
        return None
    
    try:
        status = win32serviceutil.QueryServiceStatus(ServiceClass._svc_name_)
        return status[1]  # Returns status code
    except:
        return None

if __name__ == '__main__':
    # Ensure parent directory is in path (critical for service execution)
    service_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(service_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    if len(sys.argv) == 1:
        # No arguments - try to start as service
        if PYWIN32_AVAILABLE:
            try:
                servicemanager.Initialize()
                servicemanager.PrepareToHostSingle(ServiceClass)
                servicemanager.StartServiceCtrlDispatcher()
            except Exception as e:
                # Log error to file for debugging
                from datetime import datetime
                log_path = Path(service_dir) / "service_error.log"
                with open(log_path, 'a') as f:
                    f.write(f"\n{datetime.now()}: Service start error: {e}\n")
                    import traceback
                    traceback.print_exc(file=f)
                raise
        else:
            print("pywin32 not available - cannot run as service")
    else:
        # Handle command line arguments
        if PYWIN32_AVAILABLE:
            win32serviceutil.HandleCommandLine(ServiceClass)
        else:
            print("pywin32 not available - service commands disabled")
