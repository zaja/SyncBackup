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
        
        # Import required modules
        from datetime import datetime, timedelta
        import threading
        import shutil
        
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
                                # Job should run - execute in separate thread
                                self.logger.info(f"Job '{job_data['name']}' scheduled to run - executing...")
                                
                                # Execute job in background thread
                                job_thread = threading.Thread(
                                    target=self.execute_job_background,
                                    args=(job_data, db_manager),
                                    daemon=True
                                )
                                job_thread.start()
                                
                        except Exception as e:
                            self.logger.error(f"Error checking job schedule: {e}")
                
                # Wait for 60 seconds or stop event
                if win32event.WaitForSingleObject(self.hWaitStop, 60000) == win32event.WAIT_OBJECT_0:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in service loop: {e}")
                time.sleep(60)
        
        self.logger.info("Service stopped")
    
    def execute_job_background(self, job_data, db_manager):
        """Execute job in background without GUI"""
        import shutil
        from datetime import datetime, timedelta
        from pathlib import Path
        
        job_id = job_data['id']
        job_name = job_data['name']
        job_type = job_data['job_type']
        source_path = Path(job_data['source_path'])
        dest_path = Path(job_data['dest_path'])
        
        start_time = time.time()
        
        try:
            self.logger.info(f"[Job: {job_name}] Starting execution (Type: {job_type})")
            db_manager.add_job_log(job_id, "started", f"Job started by service")
            
            files_processed = 0
            
            # Execute based on job type
            if job_type == "Simple":
                files_processed = self.execute_simple_job_service(job_data, db_manager)
            elif job_type == "Incremental":
                files_processed = self.execute_incremental_job_service(job_data, db_manager)
            else:
                raise Exception(f"Unknown job type: {job_type}")
            
            # Apply retention policies
            self.apply_retention_policies_service(job_data, db_manager)
            
            # Update last_run and calculate next_run
            last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            next_run = self.calculate_next_run_service(job_data)
            
            # Use direct SQL update to avoid NOT NULL constraint issues
            self.update_job_fields(db_manager, job_id, {
                'last_run': last_run,
                'next_run': next_run,
                'running': 0
            })
            
            duration = time.time() - start_time
            self.logger.info(f"[Job: {job_name}] Completed successfully in {duration:.2f}s")
            db_manager.add_job_log(job_id, "completed", "Job completed successfully", 
                                  duration_seconds=duration, files_processed=files_processed)
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"[Job: {job_name}] Failed: {e}")
            db_manager.add_job_log(job_id, "error", f"Job failed: {e}", 
                                  duration_seconds=duration)
            
            # Update next_run even on failure
            next_run = self.calculate_next_run_service(job_data)
            self.update_job_fields(db_manager, job_id, {
                'next_run': next_run,
                'running': 0
            })
    
    def execute_simple_job_service(self, job_data, db_manager):
        """Execute Simple job without GUI"""
        from pathlib import Path
        from datetime import datetime
        import shutil
        
        source_path = Path(job_data['source_path'])
        dest_base = Path(job_data['dest_path'])
        
        if not source_path.exists():
            raise Exception(f"Source path does not exist: {source_path}")
        
        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = source_path.name
        backup_name = f"{folder_name}_{timestamp}"
        backup_path = dest_base / backup_name
        
        # Copy files
        shutil.copytree(source_path, backup_path, dirs_exist_ok=True)
        
        # Count files
        files_processed = len([f for f in backup_path.rglob('*') if f.is_file()])
        
        # Track backup file in database
        db_manager.add_backup_file(
            job_data['id'], 
            str(backup_path), 
            'simple_backup',
            datetime.now().isoformat(),
            self.get_folder_size_service(backup_path)
        )
        
        self.logger.info(f"[Job: {job_data['name']}] Created backup: {backup_name} ({files_processed} files)")
        
        return files_processed
    
    def execute_incremental_job_service(self, job_data, db_manager):
        """Execute Incremental job without GUI - with reset_chain_after and preserve_deleted support"""
        from pathlib import Path
        from datetime import datetime
        import shutil
        import os
        import json
        import time
        
        source_path = Path(job_data['source_path'])
        dest_base = Path(job_data['dest_path'])
        folder_name = source_path.name
        job_id = job_data['id']
        reset_chain_after = job_data.get('reset_chain_after', 0)
        preserve_deleted = job_data.get('preserve_deleted', False)
        
        if not source_path.exists():
            raise Exception(f"Source path does not exist: {source_path}")
        
        self.logger.info(f"[Job: {job_data['name']}] Source: {source_path}")
        self.logger.info(f"[Job: {job_data['name']}] Destination: {dest_base}")
        
        files_processed = 0
        
        # Check if this is the first incremental backup
        hash_record = db_manager.get_backup_hash(job_id, 'incremental')
        
        # Check if we need to reset the chain
        should_reset_chain = False
        if hash_record and reset_chain_after > 0:
            incremental_count = self._count_incremental_backups_since_inicial(job_id, db_manager)
            if incremental_count >= reset_chain_after:
                should_reset_chain = True
                self.logger.info(f"[Job: {job_data['name']}] Resetting backup chain after {incremental_count} incremental backups")
        
        if not hash_record or should_reset_chain:
            # First run - create initial backup with _INICIAL suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            inicial_name = f"{folder_name}_INCREMENTAL_INICIAL_{timestamp}"
            inicial_path = dest_base / inicial_name
            
            self.logger.info(f"[Job: {job_data['name']}] Creating initial incremental backup: {inicial_name}")
            
            # Copy all files
            shutil.copytree(source_path, inicial_path, dirs_exist_ok=True)
            files_processed = sum(1 for _ in inicial_path.rglob('*') if _.is_file())
            
            # Track initial backup in database
            db_manager.add_backup_file(
                job_id,
                str(inicial_path),
                'incremental_inicial',
                datetime.now().isoformat(),
                self._get_folder_size(inicial_path)
            )
            
            # Store backup path and timestamp
            backup_info = {
                'path': str(inicial_path),
                'timestamp': time.time()
            }
            db_manager.update_backup_hash(job_id, 'incremental', json.dumps(backup_info))
            
            self.logger.info(f"[Job: {job_data['name']}] Created initial incremental backup with {files_processed} files")
        else:
            # Subsequent incremental backups - only changed files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            incremental_name = f"{folder_name}_INCREMENTAL_{timestamp}"
            incremental_path = dest_base / incremental_name
            
            # Get the last backup path to compare against
            try:
                backup_info = json.loads(hash_record['mtime'])
                last_backup_path = Path(backup_info['path'])
            except:
                self.logger.error(f"[Job: {job_data['name']}] Could not parse last backup info")
                return 0
            
            if not last_backup_path.exists():
                self.logger.error(f"[Job: {job_data['name']}] Last backup path does not exist: {last_backup_path}")
                return 0
            
            self.logger.info(f"[Job: {job_data['name']}] Creating incremental backup: {incremental_name}")
            self.logger.info(f"[Job: {job_data['name']}] Comparing against: {last_backup_path}")
            
            # Copy only changed files
            files_processed = self._copy_changed_files(source_path, incremental_path, last_backup_path)
            
            if files_processed > 0:
                # Track incremental backup in database
                db_manager.add_backup_file(
                    job_id,
                    str(incremental_path),
                    'incremental',
                    datetime.now().isoformat(),
                    self._get_folder_size(incremental_path)
                )
                
                # Update backup path and timestamp
                backup_info = {
                    'path': str(incremental_path),
                    'timestamp': time.time()
                }
                db_manager.update_backup_hash(job_id, 'incremental', json.dumps(backup_info))
                
                self.logger.info(f"[Job: {job_data['name']}] Created incremental backup with {files_processed} changed files")
            else:
                # No changes, remove empty directory
                if incremental_path.exists():
                    shutil.rmtree(incremental_path)
                self.logger.info(f"[Job: {job_data['name']}] No changes detected, skipping incremental backup")
        
        return files_processed
    
    def _copy_changed_files(self, source, dest, last_backup):
        """Copy only files that are new or modified compared to last backup"""
        import shutil
        import os
        from pathlib import Path
        
        files_processed = 0
        
        for root, dirs, files in os.walk(source):
            root_path = Path(root)
            rel_path = os.path.relpath(root, source)
            
            for file in files:
                src_file = root_path / file
                
                # Compare with last backup
                last_backup_file = last_backup / rel_path / file if rel_path != '.' else last_backup / file
                
                # Check if file is new or modified
                is_new = not last_backup_file.exists()
                is_modified = False
                
                if not is_new:
                    try:
                        # Compare modification time and size
                        src_stat = src_file.stat()
                        last_stat = last_backup_file.stat()
                        is_modified = (src_stat.st_mtime > last_stat.st_mtime or 
                                     src_stat.st_size != last_stat.st_size)
                    except:
                        is_modified = True
                
                # Copy if new or modified
                if is_new or is_modified:
                    dest_dir = dest / rel_path if rel_path != '.' else dest
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    
                    dst_file = dest_dir / file
                    shutil.copy2(src_file, dst_file)
                    files_processed += 1
                    
                    status = "new" if is_new else "modified"
                    self.logger.debug(f"Copied {status} file: {rel_path}/{file}")
        
        return files_processed
    
    def _get_folder_size(self, folder_path):
        """Get total size of folder in bytes"""
        from pathlib import Path
        total_size = 0
        try:
            for file_path in Path(folder_path).rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except:
            pass
        return total_size
    
    def _count_incremental_backups_since_inicial(self, job_id, db_manager):
        """Count incremental backups since last INICIAL"""
        try:
            import sqlite3
            with sqlite3.connect(db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Find the most recent INICIAL backup
                cursor.execute("""
                    SELECT created_at FROM backup_files
                    WHERE job_id = ? AND file_type = 'incremental_inicial'
                    ORDER BY created_at DESC LIMIT 1
                """, (job_id,))
                
                inicial_result = cursor.fetchone()
                if not inicial_result:
                    return 0
                
                inicial_time = inicial_result[0]
                
                # Count incremental backups after that INICIAL
                cursor.execute("""
                    SELECT COUNT(*) FROM backup_files
                    WHERE job_id = ? 
                    AND file_type = 'incremental'
                    AND created_at > ?
                """, (job_id, inicial_time))
                
                count_result = cursor.fetchone()
                return count_result[0] if count_result else 0
        except Exception as e:
            self.logger.error(f"Error counting incremental backups: {e}")
            return 0
    
    def calculate_next_run_service(self, job_data):
        """Calculate next run time for job"""
        from datetime import datetime, timedelta
        
        schedule_type = job_data.get('schedule_type', 'Daily')
        schedule_value = job_data.get('schedule_value', '14:00')
        
        now = datetime.now()
        
        if schedule_type == "Every X minutes":
            minutes = int(schedule_value)
            next_run = now + timedelta(minutes=minutes)
        elif schedule_type == "Every X hours":
            hours = int(schedule_value)
            next_run = now + timedelta(hours=hours)
        elif schedule_type == "Daily":
            # Parse time (HH:MM)
            hour, minute = map(int, schedule_value.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        else:
            # Default to 24 hours
            next_run = now + timedelta(days=1)
        
        return next_run.strftime("%Y-%m-%d %H:%M:%S")
    
    def get_folder_size_service(self, folder_path):
        """Get folder size in bytes"""
        from pathlib import Path
        total_size = 0
        try:
            for file_path in Path(folder_path).rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except:
            pass
        return total_size
    
    def update_job_fields(self, db_manager, job_id, fields):
        """Update specific job fields without requiring all fields"""
        import sqlite3
        
        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        
        for field, value in fields.items():
            set_clauses.append(f"{field} = ?")
            values.append(value)
        
        values.append(job_id)  # For WHERE clause
        
        query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = ?"
        
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
    
    def apply_retention_policies_service(self, job_data, db_manager):
        """Apply retention policies for job"""
        from pathlib import Path
        import shutil
        
        try:
            policies = db_manager.get_retention_policies(job_data['id'])
            
            for policy in policies:
                policy_type = policy['policy_type']
                policy_value = policy['policy_value']
                
                # Get all backup files for this job
                backup_files = db_manager.get_backup_files(job_data['id'])
                
                if job_data['job_type'] == 'Incremental':
                    # For incremental jobs, delete entire chains
                    chains = self._group_incremental_backups_into_chains(backup_files)
                    
                    if len(chains) > policy_value:
                        chains_to_delete = chains[:-policy_value]
                        self.logger.info(f"[Job: {job_data['name']}] Keeping {policy_value} most recent chains, deleting {len(chains_to_delete)} old chains")
                        
                        for chain in chains_to_delete:
                            for backup in chain:
                                try:
                                    file_path = Path(backup['file_path'])
                                    if file_path.exists():
                                        if file_path.is_dir():
                                            shutil.rmtree(file_path)
                                            self.logger.info(f"[Job: {job_data['name']}] Deleted chain folder: {file_path.name}")
                                        else:
                                            file_path.unlink()
                                    
                                    db_manager.delete_backup_file(backup['id'])
                                except Exception as e:
                                    self.logger.error(f"[Job: {job_data['name']}] Error deleting backup {backup['file_path']}: {e}")
                else:
                    # For simple jobs, delete old backups
                    if len(backup_files) > policy_value:
                        files_to_delete = backup_files[policy_value:]
                        
                        for file_info in files_to_delete:
                            try:
                                file_path = Path(file_info['file_path'])
                                if file_path.exists():
                                    if file_path.is_dir():
                                        shutil.rmtree(file_path)
                                    else:
                                        file_path.unlink()
                                    self.logger.info(f"[Job: {job_data['name']}] Deleted old backup: {file_path.name}")
                                
                                db_manager.delete_backup_file(file_info['id'])
                            except Exception as e:
                                self.logger.error(f"[Job: {job_data['name']}] Error deleting {file_info['file_path']}: {e}")
        except Exception as e:
            self.logger.error(f"[Job: {job_data['name']}] Error applying retention policies: {e}")
    
    def _group_incremental_backups_into_chains(self, backup_files):
        """Group incremental backups into chains"""
        chains = []
        current_chain = []
        
        # Sort by created_at
        sorted_backups = sorted(backup_files, key=lambda x: x['created_at'])
        
        for backup in sorted_backups:
            if backup['file_type'] == 'incremental_inicial':
                if current_chain:
                    chains.append(current_chain)
                current_chain = [backup]
            elif backup['file_type'] == 'incremental':
                current_chain.append(backup)
        
        if current_chain:
            chains.append(current_chain)
        
        return chains

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
