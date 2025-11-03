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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
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
        # Get the service script path
        service_script = os.path.abspath(__file__)
        
        # Install using HandleCommandLine
        sys.argv = ['', 'install']
        win32serviceutil.HandleCommandLine(ServiceClass)
        
        print(f"Service '{ServiceClass._svc_display_name_}' installed successfully")
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
        # Uninstall using HandleCommandLine
        sys.argv = ['', 'remove']
        win32serviceutil.HandleCommandLine(ServiceClass)
        
        print(f"Service '{ServiceClass._svc_display_name_}' uninstalled successfully")
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
    if len(sys.argv) == 1:
        # No arguments - try to start as service
        if PYWIN32_AVAILABLE:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(ServiceClass)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            print("pywin32 not available - cannot run as service")
    else:
        # Handle command line arguments
        if PYWIN32_AVAILABLE:
            win32serviceutil.HandleCommandLine(ServiceClass)
        else:
            print("pywin32 not available - service commands disabled")
