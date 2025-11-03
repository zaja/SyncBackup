#!/usr/bin/env python3
"""
SyncBackup v1.3 - Napredna aplikacija za sinkronizaciju i backup foldera

Autor: Goran Zajec
Web stranica: https://svejedobro.hr
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import threading
import time
from datetime import datetime, timedelta
import shutil
import hashlib
import schedule
from app.database import DatabaseManager
from app.language_manager import LanguageManager
from pathlib import Path
import logging
import sqlite3
import sys
import tempfile

# Set Python cache directory to app folder
import sysconfig

# Get the correct base directory for both script and executable
if getattr(sys, 'frozen', False):
    # Running as executable
    base_dir = Path(sys.executable).parent
else:
    # Running as script
    base_dir = Path(__file__).parent

cache_dir = base_dir / "app" / "__pycache__"
cache_dir.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = False  # Allow bytecode generation
os.environ['PYTHONPYCACHEPREFIX'] = str(cache_dir)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
import io
import base64

class SingleInstance:
    """Ensure only one instance of the application is running"""
    
    def __init__(self, lock_file_name="sync_backup.lock"):
        self.lock_file = Path(tempfile.gettempdir()) / lock_file_name
        self.lock_file_handle = None
    
    def __enter__(self):
        try:
            # Try to create and lock the file
            self.lock_file_handle = open(self.lock_file, 'w')
            
            # Try to acquire exclusive lock (non-blocking)
            try:
                import fcntl
                # Unix/Linux
                fcntl.flock(self.lock_file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except ImportError:
                # Windows - use msvcrt
                import msvcrt
                msvcrt.locking(self.lock_file_handle.fileno(), msvcrt.LK_NBLCK, 1)
            
            # Write PID to lock file
            self.lock_file_handle.write(str(os.getpid()))
            self.lock_file_handle.flush()
            
            return self
            
        except (OSError, IOError):
            # Another instance is already running
            if self.lock_file_handle:
                self.lock_file_handle.close()
            raise Exception("Another instance of SyncBackup is already running!")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_file_handle:
            try:
                try:
                    import fcntl
                    # Unix/Linux
                    fcntl.flock(self.lock_file_handle.fileno(), fcntl.LOCK_UN)
                except ImportError:
                    # Windows
                    import msvcrt
                    msvcrt.locking(self.lock_file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                
                self.lock_file_handle.close()
                
                # Remove lock file
                if self.lock_file.exists():
                    self.lock_file.unlink()
                    
            except (OSError, IOError):
                pass

class Job:
    """Model za backup/sync job"""
    
    def __init__(self, name="", job_type="Simple", source_path="", dest_path="", 
                 active=True, schedule_type="Daily", schedule_value="14:00",
                 preserve_deleted=False, create_snapshots=False, snapshot_interval=24,
                 exclude_patterns="", enable_notifications=True, compress_backup=False, 
                 last_run=None, next_run=None, running=False, id=None, 
                 created_at=None, updated_at=None):
        self.name = name
        self.job_type = job_type  # "Simple" ili "Incremental"
        self.source_path = source_path
        self.dest_path = dest_path
        self.active = active
        self.schedule_type = schedule_type
        self.schedule_value = schedule_value
        self.preserve_deleted = preserve_deleted
        self.create_snapshots = create_snapshots
        self.snapshot_interval = snapshot_interval
        self.exclude_patterns = exclude_patterns  # Comma-separated patterns like ".git,node_modules,__pycache__"
        self.enable_notifications = enable_notifications  # Show desktop notifications
        self.compress_backup = compress_backup  # Compress backup as ZIP file
        self.last_run = last_run
        self.next_run = next_run
        self.running = running
        self.id = id if id is not None else int(time.time() * 1000)  # Unique ID
        self.created_at = created_at
        self.updated_at = updated_at

class JobManager:
    """Upravljanje job-ovima i data persistence"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.jobs = []
        self.load_jobs()
    
    def load_jobs(self):
        """Učitaj job-ove iz baze podataka"""
        try:
            jobs_data = self.db_manager.get_jobs()
            self.jobs = []
            for job_data in jobs_data:
                # Ensure running is always False when loading
                job_data['running'] = False
                job = Job(**job_data)
                self.jobs.append(job)
        except Exception as e:
            print(f"Error loading jobs: {e}")
            import traceback
            traceback.print_exc()
            self.jobs = []
    
    def save_jobs(self):
        """Spremi job-ove u bazu podataka"""
        try:
            for job in self.jobs:
                job_dict = {
                    'name': job.name,
                    'job_type': job.job_type,
                    'source_path': job.source_path,
                    'dest_path': job.dest_path,
                    'active': job.active,
                    'schedule_type': job.schedule_type,
                    'schedule_value': job.schedule_value,
                    'preserve_deleted': job.preserve_deleted,
                    'create_snapshots': job.create_snapshots,
                    'snapshot_interval': job.snapshot_interval,
                    'last_run': job.last_run,
                    'next_run': job.next_run,
                    'running': job.running
                }
                
                if job.id:
                    self.db_manager.update_job(job.id, job_dict)
                else:
                    job.id = self.db_manager.add_job(job_dict)
        except Exception as e:
            print(f"Error saving jobs: {e}")
    
    def add_job(self, job):
        """Dodaj novi job"""
        job_dict = {
            'name': job.name,
            'job_type': job.job_type,
            'source_path': job.source_path,
            'dest_path': job.dest_path,
            'active': job.active,
            'schedule_type': job.schedule_type,
            'schedule_value': job.schedule_value,
            'preserve_deleted': job.preserve_deleted,
            'create_snapshots': job.create_snapshots,
            'snapshot_interval': job.snapshot_interval,
            'last_run': job.last_run,
            'next_run': job.next_run,
            'running': job.running
        }
        job.id = self.db_manager.add_job(job_dict)
        self.jobs.append(job)
    
    def update_job(self, job_id, updated_job):
        """Ažuriraj postojeći job"""
        job_dict = {
            'name': updated_job.name,
            'job_type': updated_job.job_type,
            'source_path': updated_job.source_path,
            'dest_path': updated_job.dest_path,
            'active': updated_job.active,
            'schedule_type': updated_job.schedule_type,
            'schedule_value': updated_job.schedule_value,
            'preserve_deleted': updated_job.preserve_deleted,
            'create_snapshots': updated_job.create_snapshots,
            'snapshot_interval': updated_job.snapshot_interval,
            'last_run': updated_job.last_run,
            'next_run': updated_job.next_run,
            'running': updated_job.running
        }
        self.db_manager.update_job(job_id, job_dict)
        
        # Update local copy
        for i, job in enumerate(self.jobs):
            if job.id == job_id:
                self.jobs[i] = updated_job
                break
    
    def delete_job(self, job_id):
        """Obriši job"""
        self.db_manager.delete_job(job_id)
        self.jobs = [job for job in self.jobs if job.id != job_id]
    
    def get_job_by_id(self, job_id):
        """Dohvati job po ID-u"""
        for job in self.jobs:
            if job.id == job_id:
                return job
        return None

class SyncBackupApp:
    """Glavna aplikacija"""
    
    @staticmethod
    def ensure_admin_privileges():
        """Ensure application runs with administrator privileges on Windows"""
        import ctypes
        
        try:
            # Check if already running as admin
            if ctypes.windll.shell32.IsUserAnAdmin():
                return  # Already admin, continue
            
            # Not admin - request elevation
            if getattr(sys, 'frozen', False):
                # Running as executable
                script = sys.executable
                params = ""
            else:
                # Running as script - use pythonw.exe to avoid console window
                python_dir = os.path.dirname(sys.executable)
                pythonw = os.path.join(python_dir, 'pythonw.exe')
                
                # Use pythonw if available, otherwise use python
                script = pythonw if os.path.exists(pythonw) else sys.executable
                script_path = os.path.abspath(sys.argv[0])
                params = f'"{script_path}"' if ' ' in script_path else script_path
            
            # Request elevation and exit current instance
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", script, params, None, 1
            )
            
            if ret > 32:
                # Successfully requested elevation, exit immediately
                os._exit(0)  # Force exit without cleanup
            else:
                # User cancelled - exit gracefully
                print("Administrator privileges required. Exiting.")
                os._exit(1)
        except Exception as e:
            print(f"Error checking admin privileges: {e}")
            os._exit(1)
    
    def __init__(self):
        # Check and request admin privileges on Windows
        if sys.platform == 'win32':
            self.ensure_admin_privileges()
        
        self.root = tk.Tk()
        self.root.geometry("1400x700")
        
        # Setup logging
        self.setup_logging()
        
        # Initialize database and job manager
        # Use correct database path for both script and executable
        if getattr(sys, 'frozen', False):
            # Running as executable
            db_path = str(base_dir / "app" / "sync_backup.db")
        else:
            # Running as script
            db_path = "app/sync_backup.db"
        
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.migrate_from_json()  # Migrate existing data
        self.job_manager = JobManager(self.db_manager)
        
        # Initialize language manager and load saved language
        self.lang_manager = LanguageManager()
        saved_language = self.db_manager.get_setting('language', 'hr')
        self.lang_manager.load_language(saved_language)
        
        # Set window title with translation and admin indicator
        title = self.lang_manager.get('window_title')
        if sys.platform == 'win32':
            import ctypes
            if ctypes.windll.shell32.IsUserAnAdmin():
                title += " [Administrator]"
        self.root.title(title)
        
        # Initialize dashboard cards early to prevent AttributeError
        self.dashboard_cards = {}
        
        # Initialize system tray
        try:
            from app.tray_icon import SystemTrayIcon
            self.tray_icon = SystemTrayIcon(self.root)
            self.tray_icon.create_tray_icon()
        except Exception as e:
            self.logger.warning(f"Could not create system tray icon: {e}")
            self.tray_icon = None
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Scheduler thread
        self.scheduler_thread = None
        self.scheduler_running = False
        
        # Notification batching thread
        self.notification_thread = None
        self.notification_running = False
        
        # Create GUI
        self.create_gui()
        
        # Start scheduler
        self.start_scheduler()
        
        # Start notification batch processor
        self.start_notification_processor()
    
    def _(self, key, default=None, **kwargs):
        """Helper method for getting translations"""
        return self.lang_manager.get(key, default, **kwargs)
    
    def setup_logging(self):
        """Setup logging sistem - only console logging, database logging handled separately"""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] [%(levelname)s] %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def create_gui(self):
        """Kreiraj glavno GUI sučelje"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(15, 10), padx=15)
        
        # Control buttons
        ttk.Button(control_frame, text=self._("buttons.new_job"), command=self.new_job_dialog).pack(side=tk.LEFT, padx=(0, 5))
        
        # Store job-specific buttons as instance variables for show/hide control
        self.edit_btn = ttk.Button(control_frame, text=self._("buttons.edit_selected"), command=self.edit_job_dialog)
        self.edit_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_btn = ttk.Button(control_frame, text=self._("buttons.delete_job"), command=self.delete_job)
        self.delete_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.open_dest_btn = ttk.Button(control_frame, text=self._("buttons.open_destination"), command=self.open_destination_folder)
        self.open_dest_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Right side buttons with colors and icons (reversed order)
        # Run Selected - Brown
        self.run_btn = tk.Button(control_frame, text=self._("buttons.run_selected"), command=self.run_job_manual,
                          bg="#8D6E63", fg="white", font=("Arial", 11, "bold"))
        self.run_btn.pack(side=tk.RIGHT, padx=(5, 15))
        
        # Deactivate Job - Red
        self.deactivate_btn = tk.Button(control_frame, text=self._("buttons.deactivate_job"), command=self.deactivate_job,
                                 bg="#F44336", fg="white", font=("Arial", 11, "bold"))
        self.deactivate_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Activate Job - Green
        self.activate_btn = tk.Button(control_frame, text=self._("buttons.activate_job"), command=self.activate_job, 
                               bg="#4CAF50", fg="white", font=("Arial", 11, "bold"))
        self.activate_btn.pack(side=tk.RIGHT, padx=(15, 0))
        
        # Store all job-specific buttons for easy control
        self.job_buttons = [self.edit_btn, self.delete_btn, self.open_dest_btn, 
                           self.run_btn, self.deactivate_btn, self.activate_btn]
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Bind tab change event to refresh backup files when needed
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Style for notebook tabs
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Arial", 11), padding=(10, 5), foreground="gray")
        style.map("TNotebook.Tab", 
                 foreground=[("selected", "black"), ("active", "black")],
                 font=[("selected", ("Arial", 11, "bold")), ("active", ("Arial", 11, "bold"))])
        
        # Dashboard tab
        self.create_dashboard_tab()
        
        # Jobs tab
        self.create_jobs_tab()
        
        # Log viewer tab
        self.create_log_tab()
        
        # Backup files tab
        self.create_backup_files_tab()
        
        # Settings tab
        self.create_settings_tab()
        
        # Load jobs into GUI
        self.refresh_jobs_list()
        
        # Refresh backup files job list
        self.refresh_backup_job_list()
        
        # Calculate next run for all active jobs
        for job in self.job_manager.jobs:
            if job.active:
                self.calculate_next_run(job)
        self.job_manager.save_jobs()
        
        # Set initial button visibility (Dashboard tab is selected by default)
        self.root.after(100, self.update_button_visibility)
    
    def create_dashboard_tab(self):
        """Kreiraj Dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text=self._("tabs.dashboard"))
        
        # Initialize dashboard cards dictionary first
        if not hasattr(self, 'dashboard_cards'):
            self.dashboard_cards = {}
        
        # Main container with padding
        main_container = ttk.Frame(dashboard_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_container, text=self._("dashboard.title"), 
                              font=("Arial", 16, "bold"), fg="#2196F3")
        title_label.pack(pady=(0, 20))
        
        # Statistics cards container
        cards_frame = ttk.Frame(main_container)
        cards_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Top row - 4 cards
        top_row = ttk.Frame(cards_frame)
        top_row.pack(fill=tk.X, pady=(0, 15))
        
        # Card 1: Total Jobs
        jobs_card = self.create_stat_card(top_row, f"📋 {self._('dashboard.total_jobs')}", "0", f"{self._('dashboard.active')}: 0", "#4CAF50")
        jobs_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Card 2: Total Backup Size
        size_card = self.create_stat_card(top_row, f"💾 {self._('dashboard.total_size')}", "0 MB", self._("dashboard.all_backups"), "#2196F3")
        size_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Card 3: Next Backup
        next_card = self.create_stat_card(top_row, f"⏰ {self._('dashboard.next_backup')}", self._("dashboard.no_active_jobs"), self._("dashboard.no_active_jobs"), "#9C27B0")
        next_card.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Bottom row - Recent Activity
        bottom_row = ttk.Frame(cards_frame)
        bottom_row.pack(fill=tk.BOTH, expand=True)
        
        # Recent Activity Card
        activity_card = ttk.LabelFrame(bottom_row, text=self._("dashboard.recent_activity"), padding=15)
        activity_card.pack(fill=tk.BOTH, expand=True)
        
        # Activity content
        self.activity_text = tk.Text(activity_card, height=8, wrap=tk.WORD, 
                                   font=("Consolas", 10), bg="#f8f9fa", 
                                   relief=tk.FLAT, bd=1)
        activity_scrollbar = ttk.Scrollbar(activity_card, orient=tk.VERTICAL, command=self.activity_text.yview)
        self.activity_text.configure(yscrollcommand=activity_scrollbar.set)
        
        self.activity_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        activity_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Auto-refresh info
        refresh_frame = ttk.Frame(main_container)
        refresh_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Auto-refresh label
        auto_refresh_label = tk.Label(refresh_frame, text="Auto-refresh: Every 30s", 
                                    font=("Arial", 9), fg="gray")
        auto_refresh_label.pack(side=tk.LEFT)
        
        # Dashboard cards are already initialized and populated
        
        # Initial refresh (delayed to ensure all widgets are created)
        self.root.after(100, self.refresh_dashboard)
        
        # Schedule auto-refresh every 30 seconds
        self.root.after(30000, self.schedule_dashboard_refresh)
    
    def create_stat_card(self, parent, title, value, subtitle, color):
        """Kreiraj statistiku karticu"""
        card_frame = ttk.LabelFrame(parent, padding=15)
        
        # Title
        title_label = tk.Label(card_frame, text=title, font=("Arial", 11, "bold"), fg=color)
        title_label.pack(anchor=tk.W)
        
        # Value
        value_label = tk.Label(card_frame, text=value, font=("Arial", 18, "bold"), fg="#333")
        value_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Subtitle
        subtitle_label = tk.Label(card_frame, text=subtitle, font=("Arial", 9), fg="gray")
        subtitle_label.pack(anchor=tk.W)
        
        # Store references for updates
        # Create unique key based on title
        if "Jobs" in title:
            card_id = "jobs"
        elif "Size" in title:
            card_id = "size"
        elif "Success" in title:
            card_id = "success"
        elif "Next" in title:
            card_id = "next"
        else:
            card_id = title.split()[1].lower()
            
        self.dashboard_cards[card_id] = {
            'value': value_label,
            'subtitle': subtitle_label
        }
        
        return card_frame
    
    def refresh_dashboard(self):
        """Osvježi Dashboard statistike"""
        try:
            # Check if dashboard is fully initialized
            if not hasattr(self, 'dashboard_cards') or len(self.dashboard_cards) < 3:
                return
            
            if not hasattr(self, 'activity_text'):
                return
            
            # Get statistics
            stats = self.get_dashboard_statistics()
            
            # Update cards
            if 'jobs' in self.dashboard_cards:
                self.dashboard_cards['jobs']['value'].config(text=str(stats['total_jobs']))
                self.dashboard_cards['jobs']['subtitle'].config(text=f"Active: {stats['active_jobs']}")
            
            if 'size' in self.dashboard_cards:
                self.dashboard_cards['size']['value'].config(text=stats['total_size_str'])
                self.dashboard_cards['size']['subtitle'].config(text="All backups")
            
            if 'next' in self.dashboard_cards:
                self.dashboard_cards['next']['value'].config(text=stats['next_backup_time'])
                self.dashboard_cards['next']['subtitle'].config(text=stats['next_backup_job'])
            
            # Update recent activity
            self.update_recent_activity(stats['recent_logs'])
            
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
    
    def get_dashboard_statistics(self):
        """Dohvati statistike za Dashboard"""
        stats = {}
        
        # Job statistics
        stats['total_jobs'] = len(self.job_manager.jobs)
        stats['active_jobs'] = sum(1 for job in self.job_manager.jobs if job.active)
        
        # Total backup size
        try:
            backup_files = self.db_manager.get_backup_files()
            total_size = sum(file.get('file_size', 0) for file in backup_files)
            
            if total_size > 1024 * 1024 * 1024:  # GB
                stats['total_size_str'] = f"{total_size / (1024 * 1024 * 1024):.1f} GB"
            elif total_size > 1024 * 1024:  # MB
                stats['total_size_str'] = f"{total_size / (1024 * 1024):.1f} MB"
            else:
                stats['total_size_str'] = f"{total_size / 1024:.1f} KB"
        except:
            stats['total_size_str'] = "0 MB"
        
        # Success rate (last 30 days)
        try:
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            logs = self.db_manager.get_job_logs()
            
            recent_logs = []
            for log in logs:
                # Use execution_time field instead of timestamp
                exec_time_str = log.get('execution_time', '')
                if exec_time_str:
                    try:
                        # Parse execution_time format: '2025-10-02 07:25:54'
                        exec_time = datetime.strptime(exec_time_str, '%Y-%m-%d %H:%M:%S')
                        if exec_time > thirty_days_ago:
                            recent_logs.append(log)
                    except:
                        continue
            
        except Exception as e:
            print(f"Error getting recent logs: {e}")
        
        # Next backup
        try:
            next_job = None
            next_time = None
            
            for job in self.job_manager.jobs:
                if job.active and job.next_run:
                    if next_time is None or job.next_run < next_time:
                        next_time = job.next_run
                        next_job = job
            
            if next_job:
                try:
                    next_dt = datetime.fromisoformat(next_time)
                    now = datetime.now()
                    
                    if next_dt > now:
                        diff = next_dt - now
                        if diff.days > 0:
                            stats['next_backup_time'] = f"{diff.days}d {diff.seconds//3600}h"
                        elif diff.seconds > 3600:
                            stats['next_backup_time'] = f"{diff.seconds//3600}h {(diff.seconds%3600)//60}m"
                        else:
                            stats['next_backup_time'] = f"{diff.seconds//60}m"
                        stats['next_backup_job'] = next_job.name
                    else:
                        stats['next_backup_time'] = "Now"
                        stats['next_backup_job'] = next_job.name
                except:
                    stats['next_backup_time'] = "Unknown"
                    stats['next_backup_job'] = next_job.name if next_job else "None"
            else:
                stats['next_backup_time'] = "None"
                stats['next_backup_job'] = "No active jobs"
        except:
            stats['next_backup_time'] = "Error"
            stats['next_backup_job'] = "Check jobs"
        
        # Recent logs for activity
        try:
            from datetime import datetime, timedelta
            yesterday = datetime.now() - timedelta(days=1)
            all_logs = self.db_manager.get_job_logs()
            
            recent_activity = []
            for log in all_logs:
                exec_time_str = log.get('execution_time', '')
                if exec_time_str:
                    try:
                        exec_time = datetime.strptime(exec_time_str, '%Y-%m-%d %H:%M:%S')
                        if exec_time > yesterday:
                            recent_activity.append(log)
                    except:
                        continue
            
            # Sort by execution_time descending
            stats['recent_logs'] = sorted(recent_activity, 
                                        key=lambda x: x.get('execution_time', ''), 
                                        reverse=True)
        except:
            stats['recent_logs'] = []
        
        return stats
    
    def update_recent_activity(self, recent_logs):
        """Ažuriraj recent activity prikaz"""
        self.activity_text.delete(1.0, tk.END)
        
        if not recent_logs:
            self.activity_text.insert(tk.END, "No recent activity in the last 24 hours.")
            return
        
        for log in recent_logs[:20]:  # Show last 20 entries
            exec_time = log.get('execution_time', '')
            job_name = log.get('job_name', 'Unknown')
            status = log.get('status', 'unknown')
            duration = log.get('duration_seconds', 0)
            
            # Format execution_time
            try:
                dt = datetime.strptime(exec_time, '%Y-%m-%d %H:%M:%S')
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = exec_time[-8:] if len(exec_time) >= 8 else exec_time
            
            # Status icon (include 'completed' as success)
            status_icon = "✅" if status in ["success", "completed"] else "❌" if status == "error" else "⏸️" if status == "skipped" else "🔄"
            
            # Duration
            duration_str = f"({duration:.1f}s)" if duration and duration > 0 else ""
            
            activity_line = f"{time_str} {status_icon} {job_name} {duration_str}\n"
            self.activity_text.insert(tk.END, activity_line)
        
        # Scroll to top
        self.activity_text.see(1.0)
    
    def schedule_dashboard_refresh(self):
        """Zakaži automatsko osvježavanje Dashboard-a"""
        self.refresh_dashboard()
        # Schedule next refresh in 30 seconds
        self.root.after(30000, self.schedule_dashboard_refresh)
    
    def create_jobs_tab(self):
        """Kreiraj Jobs tab"""
        jobs_frame = ttk.Frame(self.notebook)
        self.notebook.add(jobs_frame, text=self._("tabs.jobs"))
        
        # Treeview for jobs list
        columns = ("Name", "Type", "Source", "Destination", "Schedule", "Status", "Running", "Last Run", "Next Run")
        self.jobs_tree = ttk.Treeview(jobs_frame, columns=columns, show="headings", height=20, selectmode="extended")
        
        # Configure columns
        self.jobs_tree.heading("Name", text="Name")
        self.jobs_tree.heading("Type", text="Type")
        self.jobs_tree.heading("Source", text="Source Path")
        self.jobs_tree.heading("Destination", text="Destination Path")
        self.jobs_tree.heading("Schedule", text="Schedule")
        self.jobs_tree.heading("Status", text="Status")
        self.jobs_tree.heading("Running", text="Running")
        self.jobs_tree.heading("Last Run", text="Last Run")
        self.jobs_tree.heading("Next Run", text="Next Run")
        
        # Configure treeview style for bold headers
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), padding=(0, 8))
        style.configure("Treeview", font=("Arial", 10), rowheight=30)
        
        
        # Configure tags for row colors
        self.jobs_tree.tag_configure("active", background="#E8F5E8")
        self.jobs_tree.tag_configure("inactive", background="white")
        
        # Column widths
        self.jobs_tree.column("Name", width=150)
        self.jobs_tree.column("Type", width=80)
        self.jobs_tree.column("Source", width=200)
        self.jobs_tree.column("Destination", width=200)
        self.jobs_tree.column("Schedule", width=120)
        self.jobs_tree.column("Status", width=80)
        self.jobs_tree.column("Running", width=80)
        self.jobs_tree.column("Last Run", width=120)
        self.jobs_tree.column("Next Run", width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(jobs_frame, orient=tk.VERTICAL, command=self.jobs_tree.yview)
        self.jobs_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.jobs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Note: Removed TreeviewSelect binding to allow multiple selection
    
    def create_log_tab(self):
        """Kreiraj Log Viewer tab"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text=self._("tabs.log_viewer"))
        
        # Log control frame
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Log controls
        ttk.Button(log_control_frame, text="Refresh", command=self.refresh_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_control_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_control_frame, text="Save Log As...", command=self.save_log).pack(side=tk.LEFT, padx=(0, 5))
        
        # Filter frame
        filter_frame = ttk.Frame(log_control_frame)
        filter_frame.pack(side=tk.RIGHT)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        self.log_filter = ttk.Combobox(filter_frame, values=["All", "Errors Only", "Info Only", "Skipped Only", "Completed Only"], state="readonly")
        self.log_filter.set("All")
        self.log_filter.pack(side=tk.LEFT, padx=(0, 5))
        self.log_filter.bind("<<ComboboxSelected>>", self.filter_log)
        
        # Log text widget
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=25)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # Pack log widgets
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load initial log content
        self.refresh_log()
    
    def refresh_jobs_list(self):
        """Osvježi listu job-ova"""
        
        # Clear existing items
        for item in self.jobs_tree.get_children():
            self.jobs_tree.delete(item)
        
        
        # Add jobs
        for job in self.job_manager.jobs:
            status = "Active" if job.active else "Inactive"
            running = "Running" if job.running else "Not Running"
            last_run = job.last_run if job.last_run else "Never"
            next_run = job.next_run if job.next_run else "Not scheduled"
            
            # Determine tag based on active status
            tag = "active" if job.active else "inactive"
            
            item = self.jobs_tree.insert("", "end", values=(
                job.name,
                job.job_type,
                job.source_path,
                job.dest_path,
                f"{job.schedule_type}: {job.schedule_value}",
                status,
                running,
                last_run,
                next_run
            ), tags=(str(job.id), tag))
            
            # Color coding
            if job.active:
                self.jobs_tree.set(item, "Status", "Active")
            else:
                self.jobs_tree.set(item, "Status", "Inactive")
        
        # Refresh dashboard if it exists (only if fully initialized)
        if hasattr(self, 'dashboard_cards') and len(self.dashboard_cards) >= 4:
            try:
                self.refresh_dashboard()
            except:
                pass  # Dashboard might not be fully initialized yet
    
    def create_backup_files_tab(self):
        """Kreiraj Backup Files tab"""
        backup_frame = ttk.Frame(self.notebook)
        self.notebook.add(backup_frame, text=self._("tabs.backup_files"))
        
        # Control frame
        control_frame = ttk.Frame(backup_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Job selection
        ttk.Label(control_frame, text="Job:").pack(side=tk.LEFT, padx=(0, 5))
        self.backup_job_var = tk.StringVar()
        self.backup_job_combo = ttk.Combobox(control_frame, textvariable=self.backup_job_var, 
                                           state="readonly", width=20)
        self.backup_job_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.backup_job_combo.bind("<<ComboboxSelected>>", self.refresh_backup_files)
        
        # File type filter
        ttk.Label(control_frame, text="Type:").pack(side=tk.LEFT, padx=(0, 5))
        self.backup_type_var = tk.StringVar(value="All")
        backup_type_combo = ttk.Combobox(control_frame, textvariable=self.backup_type_var, 
                                       values=["All", "simple_backup", "incremental_snapshot"],
                                       state="readonly", width=15)
        backup_type_combo.pack(side=tk.LEFT, padx=(0, 10))
        backup_type_combo.bind("<<ComboboxSelected>>", self.refresh_backup_files)
        
        # Refresh button
        ttk.Button(control_frame, text="🔄 Refresh", command=self.refresh_backup_files).pack(side=tk.LEFT, padx=(0, 10))
        
        # Delete selected button
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_selected_backup).pack(side=tk.LEFT, padx=(0, 10))
        
        # Clean orphaned records button
        ttk.Button(control_frame, text="🧹 Clean Missing", command=self.clean_orphaned_records).pack(side=tk.LEFT)
        
        # Treeview for backup files
        columns = ("Job", "Type", "Path", "Created", "Size")
        self.backup_tree = ttk.Treeview(backup_frame, columns=columns, show="headings", height=20, selectmode="extended")
        
        # Configure columns
        self.backup_tree.heading("Job", text="Job Name")
        self.backup_tree.heading("Type", text="Type")
        self.backup_tree.heading("Path", text="File Path")
        self.backup_tree.heading("Created", text="Created")
        self.backup_tree.heading("Size", text="Size")
        
        self.backup_tree.column("Job", width=150)
        self.backup_tree.column("Type", width=120)
        self.backup_tree.column("Path", width=400)
        self.backup_tree.column("Created", width=150)
        self.backup_tree.column("Size", width=100)
        
        # Scrollbar
        backup_scrollbar = ttk.Scrollbar(backup_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=backup_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        backup_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load job names
        self.refresh_backup_job_list()
        
        # Initialize orphaned files tracking
        self.current_orphaned_files = []
    
    def refresh_backup_job_list(self):
        """Refresh job list in backup files tab"""
        job_names = ["All"] + [job.name for job in self.job_manager.jobs]
        self.backup_job_combo['values'] = job_names
        if not self.backup_job_var.get() and job_names:
            self.backup_job_var.set("All")
    
    def refresh_backup_files(self, event=None):
        """Refresh backup files list"""
        # Safety check - ensure all required components are initialized
        if not hasattr(self, 'backup_tree') or not hasattr(self, 'job_manager') or not hasattr(self, 'db_manager'):
            print("refresh_backup_files called before full initialization - skipping")
            return
            
        # Clear existing items
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        # Get filter values
        job_filter = self.backup_job_var.get()
        type_filter = self.backup_type_var.get()
        
        # Get backup files
        if job_filter == "All":
            backup_files = self.db_manager.get_backup_files()
        else:
            # Find job by name
            job_id = None
            for job in self.job_manager.jobs:
                if job.name == job_filter:
                    job_id = job.id
                    break
            
            if job_id:
                backup_files = self.db_manager.get_backup_files(job_id)
            else:
                backup_files = []
        
        # Filter by type
        if type_filter != "All":
            backup_files = [f for f in backup_files if f['file_type'] == type_filter]
        
        # Add to treeview with file existence check
        orphaned_files = []
        for file_info in backup_files:
            file_path = file_info.get('file_path', '')
            
            # Check if file exists
            file_exists = False
            if file_path:
                try:
                    file_exists = os.path.exists(file_path)
                    # Debug info
                    print(f"Checking file: {file_path} - Exists: {file_exists}")
                except Exception as e:
                    print(f"Error checking file {file_path}: {e}")
                    file_exists = False
            
            if not file_exists and file_path:
                orphaned_files.append(file_info['id'])
            
            # Format file size
            size_bytes = file_info.get('file_size', 0)
            if size_bytes > 1024 * 1024:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            elif size_bytes > 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes} B"
            
            # Format created date
            created_date = file_info.get('created_at', '')
            if created_date:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    created_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    created_str = created_date
            else:
                created_str = "Unknown"
            
            # Add visual indicator for missing files
            job_name = file_info.get('job_name', 'Unknown')
            file_type = file_info.get('file_type', 'Unknown')
            
            if not file_exists:
                job_name = f"❌ {job_name}"
                file_type = f"❌ {file_type}"
                size_str = f"❌ {size_str}"
            
            item_id = self.backup_tree.insert("", "end", values=(
                job_name,
                file_type,
                file_path,
                created_str,
                size_str
            ))
            
            # Tag missing files for different styling
            if not file_exists:
                self.backup_tree.set(item_id, "Job", f"❌ {file_info.get('job_name', 'Unknown')} (MISSING)")
        
        # Store orphaned files for cleanup
        self.current_orphaned_files = orphaned_files
        
        # Show orphaned files count if any
        if orphaned_files:
            self.show_orphaned_files_info(len(orphaned_files))
        
        # Refresh dashboard if backup files changed
        if hasattr(self, 'dashboard_cards') and self.dashboard_cards:
            try:
                self.refresh_dashboard()
            except:
                pass
    
    def delete_selected_backup(self):
        """Delete selected backup file(s)"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select one or more backup files to delete.")
            return
        
        # Get all selected file paths
        files_to_delete = []
        for item in selection:
            item_data = self.backup_tree.item(item)
            file_path = item_data['values'][2]  # Path is in column 2
            files_to_delete.append(file_path)
        
        # Confirm deletion
        if len(files_to_delete) == 1:
            confirm_msg = f"Are you sure you want to delete:\n{files_to_delete[0]}?"
        else:
            confirm_msg = f"Are you sure you want to delete {len(files_to_delete)} backup files?"
        
        if messagebox.askyesno("Confirm Delete", confirm_msg):
            deleted_count = 0
            errors = []
            
            for file_path in files_to_delete:
                try:
                    # Delete from filesystem
                    from pathlib import Path
                    path = Path(file_path)
                    if path.exists():
                        if path.is_dir():
                            import shutil
                            shutil.rmtree(path)
                        else:
                            path.unlink()
                    
                    # Delete from database
                    backup_files = self.db_manager.get_backup_files()
                    for backup_file in backup_files:
                        if backup_file['file_path'] == file_path:
                            self.db_manager.delete_backup_file(backup_file['id'])
                            break
                    
                    deleted_count += 1
                    
                except Exception as e:
                    errors.append(f"{file_path}: {str(e)}")
            
            # Refresh the list
            self.refresh_backup_files()
            
            # Show results
            if deleted_count > 0:
                success_msg = f"Successfully deleted {deleted_count} backup file(s)."
                if errors:
                    success_msg += f"\n\nErrors occurred with {len(errors)} file(s):\n" + "\n".join(errors)
                    messagebox.showwarning("Partial Success", success_msg)
                else:
                    messagebox.showinfo("Success", success_msg)
            else:
                messagebox.showerror("Error", f"Failed to delete any files:\n" + "\n".join(errors))
    
    def show_orphaned_files_info(self, count):
        """Show information about orphaned files"""
        # This could be expanded to show in status bar or as a tooltip
        # For now, we'll just store the count for the clean function
        pass
    
    def clean_orphaned_records(self):
        """Clean orphaned database records for non-existent backup files"""
        if not hasattr(self, 'current_orphaned_files') or not self.current_orphaned_files:
            messagebox.showinfo("Clean Missing", "No missing backup files found in current view.")
            return
        
        count = len(self.current_orphaned_files)
        if messagebox.askyesno("Clean Missing Files", 
                              f"Found {count} database records for missing backup files.\n\n"
                              f"Do you want to remove these orphaned records from the database?\n\n"
                              f"Note: This will only remove database entries, not actual files."):
            
            cleaned_count = 0
            errors = []
            
            for file_id in self.current_orphaned_files:
                try:
                    self.db_manager.delete_backup_file(file_id)
                    cleaned_count += 1
                except Exception as e:
                    errors.append(f"ID {file_id}: {str(e)}")
            
            # Refresh the list
            self.refresh_backup_files()
            
            # Show results
            if cleaned_count > 0:
                success_msg = f"Successfully cleaned {cleaned_count} orphaned record(s)."
                if errors:
                    success_msg += f"\n\nErrors occurred with {len(errors)} record(s):\n" + "\n".join(errors)
                    messagebox.showwarning("Partial Success", success_msg)
                else:
                    messagebox.showinfo("Success", success_msg)
            else:
                messagebox.showerror("Error", f"Failed to clean any records:\n" + "\n".join(errors))
    
    def create_settings_tab(self):
        """Kreiraj Settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text=self._("tabs.settings"))
        
        # Create canvas with scrollbar for scrollable content
        canvas = tk.Canvas(settings_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Main container with padding
        main_container = ttk.Frame(scrollable_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        # Title
        title_label = tk.Label(main_container, text=self._("settings.title"), 
                              font=("Arial", 16, "bold"), fg="#2196F3")
        title_label.pack(pady=(0, 30))
        
        # Language Settings Section
        lang_frame = ttk.LabelFrame(main_container, text=self._("settings.language_section"), padding=20)
        lang_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(lang_frame, text=self._("settings.select_language"), font=("Arial", 10)).pack(anchor=tk.W, pady=(0, 10))
        
        self.language_var = tk.StringVar(value=self.lang_manager.get_current_language())
        
        lang_options_frame = ttk.Frame(lang_frame)
        lang_options_frame.pack(anchor=tk.W)
        
        # Dynamically create radio buttons for all available languages
        available_languages = self.lang_manager.get_available_languages()
        for i, (code, name) in enumerate(available_languages.items()):
            padx = (0, 20) if i < len(available_languages) - 1 else (0, 0)
            ttk.Radiobutton(lang_options_frame, text=name, 
                           variable=self.language_var, value=code).pack(side=tk.LEFT, padx=padx)
        
        ttk.Label(lang_frame, text=self._("settings.language_note"), 
                 font=("Arial", 9), foreground="gray").pack(anchor=tk.W, pady=(10, 0))
        
        # Notification Settings Section
        notif_frame = ttk.LabelFrame(main_container, text=self._("settings.notification_section"), padding=20)
        notif_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(notif_frame, text=self._("settings.notification_mode"), font=("Arial", 10)).pack(anchor=tk.W, pady=(0, 10))
        
        self.notification_mode_var = tk.StringVar(value=self.db_manager.get_setting('notification_mode', 'batch'))
        
        notif_options_frame = ttk.Frame(notif_frame)
        notif_options_frame.pack(anchor=tk.W, fill=tk.X)
        
        ttk.Radiobutton(notif_options_frame, text=self._("settings.immediate"), 
                       variable=self.notification_mode_var, value='immediate').pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(notif_options_frame, text=self._("settings.batch"), 
                       variable=self.notification_mode_var, value='batch').pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(notif_options_frame, text=self._("settings.disabled"), 
                       variable=self.notification_mode_var, value='disabled').pack(anchor=tk.W, pady=2)
        
        # Batch interval setting
        batch_interval_frame = ttk.Frame(notif_frame)
        batch_interval_frame.pack(anchor=tk.W, pady=(10, 0))
        
        ttk.Label(batch_interval_frame, text=self._("settings.batch_interval")).pack(side=tk.LEFT, padx=(0, 10))
        
        self.batch_interval_var = tk.StringVar(value=self.db_manager.get_setting('notification_batch_interval', '300'))
        batch_interval_spinbox = ttk.Spinbox(batch_interval_frame, from_=60, to=3600, increment=60, 
                                            textvariable=self.batch_interval_var, width=10)
        batch_interval_spinbox.pack(side=tk.LEFT)
        
        ttk.Label(notif_frame, text=self._("settings.batch_note"), 
                 font=("Arial", 9), foreground="gray").pack(anchor=tk.W, pady=(10, 0))
        
        # Service Settings Section (Windows only)
        if sys.platform == 'win32':
            service_frame = ttk.LabelFrame(main_container, text=self._("settings.service_section"), padding=20)
            service_frame.pack(fill=tk.X, pady=(0, 20))
            
            # Service status indicator
            status_frame = ttk.Frame(service_frame)
            status_frame.pack(anchor=tk.W, pady=(0, 15))
            
            ttk.Label(status_frame, text=self._("settings.run_as_service"), font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 10))
            
            # Check service status and show indicator
            self.service_status_label = tk.Label(status_frame, text="", font=("Arial", 10, "bold"))
            self.service_status_label.pack(side=tk.LEFT)
            self.update_service_status_indicator()
            
            # Refresh button for status
            ttk.Button(status_frame, text="🔄", width=3, 
                      command=self.update_service_status_indicator).pack(side=tk.LEFT, padx=(5, 0))
            
            self.run_as_service_var = tk.BooleanVar(value=self.db_manager.get_setting('run_as_service', '0') == '1')
            
            ttk.Checkbutton(service_frame, text=self._("settings.enable_service"), 
                           variable=self.run_as_service_var).pack(anchor=tk.W)
            
            ttk.Label(service_frame, text=self._("settings.service_note"), 
                     font=("Arial", 9), foreground="gray").pack(anchor=tk.W, pady=(10, 0))
            
            # Service control buttons - Row 1: Install/Uninstall/Status
            service_btn_frame1 = ttk.Frame(service_frame)
            service_btn_frame1.pack(anchor=tk.W, pady=(15, 5))
            
            ttk.Button(service_btn_frame1, text=self._("buttons.install_service"), 
                      command=self.install_service).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(service_btn_frame1, text=self._("buttons.uninstall_service"), 
                      command=self.uninstall_service).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(service_btn_frame1, text=self._("buttons.service_status"), 
                      command=self.check_service_status).pack(side=tk.LEFT)
            
            # Service control buttons - Row 2: Start/Stop/Restart
            service_btn_frame2 = ttk.Frame(service_frame)
            service_btn_frame2.pack(anchor=tk.W, pady=(5, 0))
            
            ttk.Button(service_btn_frame2, text="▶ Start Service", 
                      command=self.start_service_action).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(service_btn_frame2, text="⏸ Stop Service", 
                      command=self.stop_service_action).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(service_btn_frame2, text="🔄 Restart Service", 
                      command=self.restart_service_action).pack(side=tk.LEFT)
        
        # Save button
        save_btn_frame = ttk.Frame(main_container)
        save_btn_frame.pack(pady=(20, 0))
        
        ttk.Button(save_btn_frame, text=self._("buttons.save_settings"), 
                  command=self.save_settings, style="Accent.TButton").pack()
        
        # Configure accent button style
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 11, "bold"))
    
    def update_service_status_indicator(self):
        """Update service status indicator in Settings tab"""
        if not hasattr(self, 'service_status_label'):
            return
        
        try:
            from app.windows_service import is_service_running, get_service_status, PYWIN32_AVAILABLE
            
            if not PYWIN32_AVAILABLE:
                self.service_status_label.config(text="⚪ Not Available", fg="gray")
                return
            
            if is_service_running():
                self.service_status_label.config(text="🟢 Running", fg="green")
            else:
                status = get_service_status()
                if "Not installed" in status or "error" in status.lower():
                    self.service_status_label.config(text="⚪ Not Installed", fg="gray")
                else:
                    self.service_status_label.config(text=f"🔴 {status}", fg="red")
        except Exception as e:
            self.service_status_label.config(text="⚪ Unknown", fg="gray")
    
    def save_settings(self):
        """Save application settings"""
        try:
            # Save language
            self.db_manager.set_setting('language', self.language_var.get())
            
            # Save notification settings
            self.db_manager.set_setting('notification_mode', self.notification_mode_var.get())
            self.db_manager.set_setting('notification_batch_interval', self.batch_interval_var.get())
            
            # Save service setting if on Windows
            if sys.platform == 'win32' and hasattr(self, 'run_as_service_var'):
                self.db_manager.set_setting('run_as_service', '1' if self.run_as_service_var.get() else '0')
            
            messagebox.showinfo(self._("messages.success"), self._("messages.settings_saved"))
        except Exception as e:
            messagebox.showerror(self._("messages.error"), f"Failed to save settings:\n{e}")
    
    def install_service(self):
        """Install Windows service"""
        try:
            from app.windows_service import install_service, PYWIN32_AVAILABLE
            
            if not PYWIN32_AVAILABLE:
                messagebox.showerror("Service Installation", 
                                   "pywin32 is not installed.\n\n"
                                   "Please install it with:\npip install pywin32")
                return
            
            if messagebox.askyesno("Install Service", 
                                  "This will install SyncBackup as a Windows Service.\n\n"
                                  "The service will run in the background and start automatically with Windows.\n\n"
                                  "Continue?"):
                if install_service():
                    messagebox.showinfo("Success", 
                                      "Service installed successfully!\n\n"
                                      "You can start it from the Service Status button or from Windows Services.")
                    self.update_service_status_indicator()  # Refresh status
                else:
                    messagebox.showerror("Error", "Failed to install service. Check console for details.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install service:\n{e}")
    
    def uninstall_service(self):
        """Uninstall Windows service"""
        try:
            from app.windows_service import uninstall_service, stop_service, PYWIN32_AVAILABLE
            
            if not PYWIN32_AVAILABLE:
                messagebox.showerror("Service Uninstallation", 
                                   "pywin32 is not installed.")
                return
            
            if messagebox.askyesno("Uninstall Service", 
                                  "This will uninstall the SyncBackup Windows Service.\n\n"
                                  "Continue?"):
                # Try to stop service first
                stop_service()
                
                if uninstall_service():
                    messagebox.showinfo("Success", "Service uninstalled successfully!")
                    self.update_service_status_indicator()  # Refresh status
                else:
                    messagebox.showerror("Error", "Failed to uninstall service. Check console for details.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to uninstall service:\n{e}")
    
    def check_service_status(self):
        """Check Windows service status"""
        try:
            from app.windows_service import get_service_status, PYWIN32_AVAILABLE
            
            if not PYWIN32_AVAILABLE:
                messagebox.showinfo("Service Status", 
                                  "pywin32 is not installed.\n\n"
                                  "Service functionality is not available.")
                return
            
            status = get_service_status()
            messagebox.showinfo("Service Status", 
                              f"SyncBackup Windows Service\n\n"
                              f"Status: {status}\n\n"
                              f"Note: You can also check the service status in Windows Services (services.msc)")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check service status:\n{e}")
    
    def start_service_action(self):
        """Start Windows service"""
        try:
            from app.windows_service import start_service, PYWIN32_AVAILABLE
            
            if not PYWIN32_AVAILABLE:
                messagebox.showerror("Error", "pywin32 is not installed.")
                return
            
            if start_service():
                messagebox.showinfo("Success", "Service started successfully!")
                self.update_service_status_indicator()
            else:
                messagebox.showerror("Error", "Failed to start service.\n\nCheck if service is installed.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start service:\n{e}")
    
    def stop_service_action(self):
        """Stop Windows service"""
        try:
            from app.windows_service import stop_service, PYWIN32_AVAILABLE
            
            if not PYWIN32_AVAILABLE:
                messagebox.showerror("Error", "pywin32 is not installed.")
                return
            
            if messagebox.askyesno("Stop Service", 
                                  "Are you sure you want to stop the service?\n\n"
                                  "Scheduled backups will not run while the service is stopped."):
                if stop_service():
                    messagebox.showinfo("Success", "Service stopped successfully!")
                    self.update_service_status_indicator()
                else:
                    messagebox.showerror("Error", "Failed to stop service.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop service:\n{e}")
    
    def restart_service_action(self):
        """Restart Windows service"""
        try:
            from app.windows_service import stop_service, start_service, PYWIN32_AVAILABLE
            
            if not PYWIN32_AVAILABLE:
                messagebox.showerror("Error", "pywin32 is not installed.")
                return
            
            # Stop service
            stop_service()
            
            # Wait a moment
            import time
            time.sleep(2)
            
            # Start service
            if start_service():
                messagebox.showinfo("Success", "Service restarted successfully!")
                self.update_service_status_indicator()
            else:
                messagebox.showerror("Error", "Failed to restart service.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart service:\n{e}")
    
    def update_button_visibility(self):
        """Update button visibility based on current tab"""
        try:
            if not hasattr(self, 'job_buttons') or not hasattr(self, 'notebook'):
                return
                
            selected_tab = self.notebook.select()
            tab_text = self.notebook.tab(selected_tab, "text")
            
            # Show job buttons only on Jobs tab
            if "Jobs" in tab_text:
                # Show buttons by re-packing them in correct order
                self.edit_btn.pack(side=tk.LEFT, padx=(0, 5))
                self.delete_btn.pack(side=tk.LEFT, padx=(0, 5))
                self.open_dest_btn.pack(side=tk.LEFT, padx=(0, 5))
                
                # Right side buttons (pack in reverse order)
                self.run_btn.pack(side=tk.RIGHT, padx=(5, 15))
                self.deactivate_btn.pack(side=tk.RIGHT, padx=(5, 0))
                self.activate_btn.pack(side=tk.RIGHT, padx=(15, 0))
            else:
                # Hide job buttons on other tabs
                for button in self.job_buttons:
                    button.pack_forget()
        except Exception as e:
            print(f"Error updating button visibility: {e}")
    
    def on_tab_changed(self, event):
        """Handle tab change events"""
        try:
            # Only process if GUI is fully initialized
            if not hasattr(self, 'backup_tree') or not hasattr(self, 'job_manager'):
                return
                
            selected_tab = self.notebook.select()
            tab_text = self.notebook.tab(selected_tab, "text")
            
            # Update button visibility based on current tab
            self.update_button_visibility()
            
            # Refresh backup files when switching to Backup Files tab
            if tab_text == "Backup Files":
                print("Switching to Backup Files tab - refreshing...")
                self.refresh_backup_files()
        except Exception as e:
            print(f"Error in tab change handler: {e}")
    
    
    def new_job_dialog(self):
        """Otvori dijalog za novi job"""
        self.job_dialog(None)
    
    def edit_job_dialog(self):
        """Otvori dijalog za uređivanje job-a"""
        selection = self.jobs_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a job to edit.")
            return
        
        if len(selection) > 1:
            messagebox.showwarning("Warning", "Please select only one job to edit.")
            return
        
        # Get the selected job
        item = selection[0]
        job_id = int(self.jobs_tree.item(item, "tags")[0])
        job = self.job_manager.get_job_by_id(job_id)
        if job:
            self.job_dialog(job)
    
    def job_dialog(self, job=None):
        """Job creation/editing dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Job" if job else "New Job")
        dialog.geometry("500x950")
        dialog.resizable(False, False)
        
        # Position dialog relative to main window
        dialog.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        dialog.geometry(f"500x950+{main_x+50}+{main_y+50}")
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Job name
        ttk.Label(main_frame, text="Job Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        name_var = tk.StringVar(value=job.name if job else "")
        name_entry = ttk.Entry(main_frame, textvariable=name_var, width=40)
        name_entry.grid(row=0, column=1, columnspan=2, sticky=tk.W+tk.E, pady=(0, 5))
        ttk.Label(main_frame, text="Enter a descriptive name for this backup job", 
                 font=("Arial", 9), foreground="gray").grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Job type
        ttk.Label(main_frame, text="Job Type:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        type_var = tk.StringVar(value=job.job_type if job else "Simple")
        type_frame = ttk.Frame(main_frame)
        type_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=(0, 5))
        ttk.Radiobutton(type_frame, text="Simple", variable=type_var, value="Simple").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(type_frame, text="Incremental", variable=type_var, value="Incremental").pack(side=tk.LEFT)
        ttk.Label(main_frame, text="Simple: Full backup each time | Incremental: Sync changes only", 
                 font=("Arial", 9), foreground="gray").grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Source path
        ttk.Label(main_frame, text="Source Path:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        source_var = tk.StringVar(value=job.source_path if job else "")
        source_entry = ttk.Entry(main_frame, textvariable=source_var, width=30)
        source_entry.grid(row=4, column=1, sticky=tk.W+tk.E, pady=(0, 5))
        ttk.Button(main_frame, text="Browse", command=lambda: self.browse_folder(source_var)).grid(row=4, column=2, padx=(5, 0), pady=(0, 5))
        ttk.Label(main_frame, text="Folder to backup", 
                 font=("Arial", 9), foreground="gray").grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Destination path
        ttk.Label(main_frame, text="Destination Path:").grid(row=6, column=0, sticky=tk.W, pady=(0, 5))
        dest_var = tk.StringVar(value=job.dest_path if job else "")
        dest_entry = ttk.Entry(main_frame, textvariable=dest_var, width=30)
        dest_entry.grid(row=6, column=1, sticky=tk.W+tk.E, pady=(0, 5))
        ttk.Button(main_frame, text="Browse", command=lambda: self.browse_folder(dest_var)).grid(row=6, column=2, padx=(5, 0), pady=(0, 5))
        ttk.Label(main_frame, text="Where to store backups", 
                 font=("Arial", 9), foreground="gray").grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Active checkbox
        active_var = tk.BooleanVar(value=job.active if job else True)
        ttk.Checkbutton(main_frame, text="Active", variable=active_var).grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Notifications checkbox
        notifications_var = tk.BooleanVar(value=job.enable_notifications if job else True)
        ttk.Checkbutton(main_frame, text="Show desktop notifications", variable=notifications_var).grid(row=8, column=2, sticky=tk.W, pady=(0, 5))
        
        # Compression checkbox (only for Simple jobs)
        compress_var = tk.BooleanVar(value=job.compress_backup if job else False)
        compress_check = ttk.Checkbutton(main_frame, text="Compress backup as ZIP (Simple jobs only)", variable=compress_var)
        compress_check.grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Function to toggle compression based on job type
        def toggle_compression_option(*args):
            job_type = type_var.get()
            if job_type == "Simple":
                compress_check.configure(state="normal")
            else:
                compress_check.configure(state="disabled")
                compress_var.set(False)  # Disable compression for Incremental jobs
        
        # Bind job type change to toggle compression
        type_var.trace('w', toggle_compression_option)
        toggle_compression_option()  # Initial call
        
        # Exclude patterns
        ttk.Label(main_frame, text="Exclude Patterns:").grid(row=10, column=0, sticky=tk.W, pady=(0, 5))
        exclude_var = tk.StringVar(value=job.exclude_patterns if job else ".git,node_modules,__pycache__,.DS_Store,Thumbs.db")
        exclude_entry = ttk.Entry(main_frame, textvariable=exclude_var, width=40)
        exclude_entry.grid(row=10, column=1, columnspan=2, sticky=tk.W+tk.E, pady=(0, 5))
        ttk.Label(main_frame, text="Comma-separated patterns to exclude (e.g., .git,node_modules,*.tmp)", 
                 font=("Arial", 9), foreground="gray").grid(row=11, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Schedule section
        ttk.Label(main_frame, text="Schedule:", font=("TkDefaultFont", 10, "bold")).grid(row=12, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        # Schedule type
        ttk.Label(main_frame, text="Schedule Type:").grid(row=13, column=0, sticky=tk.W, pady=(0, 5))
        schedule_type_var = tk.StringVar(value=job.schedule_type if job else "Daily")
        schedule_type_combo = ttk.Combobox(main_frame, textvariable=schedule_type_var, 
                                         values=["Every X minutes", "Every X hours", "Daily at specific time", 
                                                "Weekly on specific days", "Monthly on specific day"], 
                                         state="readonly", width=25)
        schedule_type_combo.grid(row=12, column=1, columnspan=2, sticky=tk.W, pady=(0, 5))
        ttk.Label(main_frame, text="How often to run the backup", 
                 font=("Arial", 9), foreground="gray").grid(row=13, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Schedule value
        ttk.Label(main_frame, text="Schedule Value:").grid(row=14, column=0, sticky=tk.W, pady=(0, 5))
        schedule_value_var = tk.StringVar(value=job.schedule_value if job else "14:00")
        schedule_value_entry = ttk.Entry(main_frame, textvariable=schedule_value_var, width=25)
        schedule_value_entry.grid(row=14, column=1, columnspan=2, sticky=tk.W, pady=(0, 5))
        ttk.Label(main_frame, text="Minutes/hours or time (HH:MM)", 
                 font=("Arial", 9), foreground="gray").grid(row=15, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Incremental options (only for Incremental jobs)
        incremental_frame = ttk.LabelFrame(main_frame, text="Incremental Options")
        incremental_frame.grid(row=16, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(10, 5))
        
        preserve_deleted_var = tk.BooleanVar(value=job.preserve_deleted if job else False)
        preserve_deleted_check = ttk.Checkbutton(incremental_frame, text="Preserve deleted files on destination", 
                       variable=preserve_deleted_var)
        preserve_deleted_check.pack(anchor=tk.W, padx=5, pady=2)
        
        create_snapshots_var = tk.BooleanVar(value=job.create_snapshots if job else False)
        create_snapshots_check = ttk.Checkbutton(incremental_frame, text="Create periodic snapshots", 
                       variable=create_snapshots_var)
        create_snapshots_check.pack(anchor=tk.W, padx=5, pady=2)
        
        snapshot_frame = ttk.Frame(incremental_frame)
        snapshot_frame.pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(snapshot_frame, text="Every").pack(side=tk.LEFT)
        snapshot_interval_var = tk.StringVar(value=str(job.snapshot_interval) if job else "24")
        snapshot_interval_entry = ttk.Entry(snapshot_frame, textvariable=snapshot_interval_var, width=5)
        snapshot_interval_entry.pack(side=tk.LEFT, padx=(5, 5))
        snapshot_unit_var = tk.StringVar(value="hours")
        snapshot_unit_combo = ttk.Combobox(snapshot_frame, textvariable=snapshot_unit_var, values=["hours", "days", "weeks"], 
                    state="readonly", width=8)
        snapshot_unit_combo.pack(side=tk.LEFT)
        
        # Function to toggle incremental options
        def toggle_incremental_options():
            if type_var.get() == "Incremental":
                preserve_deleted_check.configure(state="normal")
                create_snapshots_check.configure(state="normal")
                snapshot_interval_entry.configure(state="normal")
                snapshot_unit_combo.configure(state="readonly")
            else:
                preserve_deleted_check.configure(state="disabled")
                create_snapshots_check.configure(state="disabled")
                snapshot_interval_entry.configure(state="disabled")
                snapshot_unit_combo.configure(state="disabled")
        
        # Bind the radio buttons to toggle function
        type_var.trace('w', lambda *args: toggle_incremental_options())
        
        # Initial state
        toggle_incremental_options()
        
        # Retention Policy Options
        retention_frame = ttk.LabelFrame(main_frame, text="Retention Policy")
        retention_frame.grid(row=17, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(10, 5))
        
        # Enable retention policy
        enable_retention_var = tk.BooleanVar(value=False)
        enable_retention_check = ttk.Checkbutton(retention_frame, text="Enable file retention policy", 
                       variable=enable_retention_var)
        enable_retention_check.pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(retention_frame, text="Automatically delete old backup files based on rules below", 
                 font=("Arial", 9), foreground="gray").pack(anchor=tk.W, padx=5, pady=(0, 5))
        
        # Retention policy type
        retention_type_var = tk.StringVar(value="keep_count")
        retention_type_frame = ttk.Frame(retention_frame)
        retention_type_frame.pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(retention_type_frame, text="Keep:").pack(side=tk.LEFT)
        ttk.Radiobutton(retention_type_frame, text="Last N backups", variable=retention_type_var, value="keep_count").pack(side=tk.LEFT, padx=(5, 10))
        ttk.Radiobutton(retention_type_frame, text="Backups for N days", variable=retention_type_var, value="keep_days").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(retention_type_frame, text="Until N MB", variable=retention_type_var, value="keep_size").pack(side=tk.LEFT)
        
        # Helper text for retention types
        ttk.Label(retention_frame, text="Last N backups: Keep only the most recent backup files", 
                 font=("Arial", 9), foreground="gray").pack(anchor=tk.W, padx=5, pady=(0, 2))
        ttk.Label(retention_frame, text="Backups for N days: Keep backups created within the last N days", 
                 font=("Arial", 9), foreground="gray").pack(anchor=tk.W, padx=5, pady=(0, 2))
        ttk.Label(retention_frame, text="Until N MB: Keep backups until total size exceeds N MB", 
                 font=("Arial", 9), foreground="gray").pack(anchor=tk.W, padx=5, pady=(0, 5))
        
        # Retention policy value
        retention_value_frame = ttk.Frame(retention_frame)
        retention_value_frame.pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(retention_value_frame, text="Value:").pack(side=tk.LEFT)
        retention_value_var = tk.StringVar(value="10")
        retention_value_entry = ttk.Entry(retention_value_frame, textvariable=retention_value_var, width=10)
        retention_value_entry.pack(side=tk.LEFT, padx=(5, 5))
        retention_unit_label = ttk.Label(retention_value_frame, text="backups")
        retention_unit_label.pack(side=tk.LEFT)
        
        # Helper text for value
        ttk.Label(retention_frame, text="Enter the number of backups, days, or MB to keep", 
                 font=("Arial", 9), foreground="gray").pack(anchor=tk.W, padx=5, pady=(0, 5))
        
        # Function to update retention unit label
        def update_retention_unit(*args):
            policy_type = retention_type_var.get()
            if policy_type == "keep_count":
                retention_unit_label.config(text="backups")
            elif policy_type == "keep_days":
                retention_unit_label.config(text="days")
            elif policy_type == "keep_size":
                retention_unit_label.config(text="MB")
        
        # Function to toggle retention policy options
        def toggle_retention_options(*args):
            enabled = enable_retention_var.get()
            if enabled:
                # Enable radio buttons
                for widget in retention_type_frame.winfo_children():
                    if isinstance(widget, ttk.Radiobutton):
                        widget.configure(state="normal")
                retention_value_entry.configure(state="normal")
            else:
                # Disable radio buttons
                for widget in retention_type_frame.winfo_children():
                    if isinstance(widget, ttk.Radiobutton):
                        widget.configure(state="disabled")
                retention_value_entry.configure(state="disabled")
        
        retention_type_var.trace('w', update_retention_unit)
        enable_retention_var.trace('w', toggle_retention_options)
        update_retention_unit()  # Initial call
        toggle_retention_options()  # Initial call
        
        # Load existing retention policy if editing
        if job:
            existing_policies = self.db_manager.get_retention_policies(job.id)
            if existing_policies:
                policy = existing_policies[0]  # Take first policy
                enable_retention_var.set(True)
                retention_type_var.set(policy['policy_type'])
                retention_value_var.set(str(policy['policy_value']))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=18, column=0, columnspan=3, pady=(35, 0))
        
        def save_job():
            # Validation
            if not name_var.get().strip():
                messagebox.showerror("Error", "Job name is required.")
                return
            
            if not source_var.get().strip():
                messagebox.showerror("Error", "Source path is required.")
                return
            
            if not dest_var.get().strip():
                messagebox.showerror("Error", "Destination path is required.")
                return
            
            if not os.path.exists(source_var.get()):
                messagebox.showerror("Error", "Source path does not exist.")
                return
            
            # Create or update job
            if job:
                # Update existing job
                job.name = name_var.get().strip()
                job.job_type = type_var.get()
                job.source_path = source_var.get().strip()
                job.dest_path = dest_var.get().strip()
                job.active = active_var.get()
                job.schedule_type = schedule_type_var.get()
                job.schedule_value = schedule_value_var.get()
                job.preserve_deleted = preserve_deleted_var.get()
                job.create_snapshots = create_snapshots_var.get()
                job.snapshot_interval = int(snapshot_interval_var.get())
                job.exclude_patterns = exclude_var.get().strip()
                job.enable_notifications = notifications_var.get()
                job.compress_backup = compress_var.get()
                
                self.job_manager.update_job(job.id, job)
                
                # Update retention policy
                existing_policies = self.db_manager.get_retention_policies(job.id)
                
                if enable_retention_var.get():
                    try:
                        policy_value = int(retention_value_var.get())
                        if existing_policies:
                            # Update existing policy
                            self.db_manager.update_retention_policy(
                                existing_policies[0]['id'],
                                retention_type_var.get(),
                                policy_value,
                                True
                            )
                        else:
                            # Add new policy
                            self.db_manager.add_retention_policy(
                                job.id, 
                                retention_type_var.get(), 
                                policy_value
                            )
                    except ValueError:
                        messagebox.showerror("Error", "Retention policy value must be a number.")
                        return
                else:
                    # Disable existing policy
                    if existing_policies:
                        self.db_manager.update_retention_policy(
                            existing_policies[0]['id'],
                            enabled=False
                        )
            else:
                # Create new job
                new_job = Job(
                    name=name_var.get().strip(),
                    job_type=type_var.get(),
                    source_path=source_var.get().strip(),
                    dest_path=dest_var.get().strip(),
                    active=active_var.get(),
                    schedule_type=schedule_type_var.get(),
                    schedule_value=schedule_value_var.get(),
                    preserve_deleted=preserve_deleted_var.get(),
                    create_snapshots=create_snapshots_var.get(),
                    snapshot_interval=int(snapshot_interval_var.get()),
                    exclude_patterns=exclude_var.get().strip(),
                    enable_notifications=notifications_var.get(),
                    compress_backup=compress_var.get()
                )
                self.job_manager.add_job(new_job)
                
                # Add retention policy if enabled
                if enable_retention_var.get():
                    try:
                        policy_value = int(retention_value_var.get())
                        self.db_manager.add_retention_policy(
                            new_job.id, 
                            retention_type_var.get(), 
                            policy_value
                        )
                    except ValueError:
                        messagebox.showerror("Error", "Retention policy value must be a number.")
                        return
                
                # Calculate next run for new job if it's active
                if new_job.active:
                    self.calculate_next_run(new_job)
                    self.job_manager.save_jobs()
            
            self.refresh_jobs_list()
            dialog.destroy()
        
        ttk.Button(button_frame, text="Save", command=save_job).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Test Paths", command=lambda: self.test_paths(source_var.get(), dest_var.get())).pack(side=tk.LEFT, padx=(10, 0))
    
    def browse_folder(self, var):
        """Browse za folder"""
        folder = filedialog.askdirectory()
        if folder:
            var.set(folder)
    
    def test_paths(self, source, dest):
        """Test putanja"""
        if not source or not dest:
            messagebox.showerror("Error", "Please enter both source and destination paths.")
            return
        
        errors = []
        if not os.path.exists(source):
            errors.append(f"Source path does not exist: {source}")
        elif not os.path.isdir(source):
            errors.append(f"Source path is not a directory: {source}")
        
        if not os.path.exists(dest):
            try:
                os.makedirs(dest, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create destination directory: {e}")
        elif not os.path.isdir(dest):
            errors.append(f"Destination path is not a directory: {dest}")
        
        if errors:
            messagebox.showerror("Path Test Failed", "\n".join(errors))
        else:
            messagebox.showinfo("Path Test", "Both paths are valid and accessible.")
    
    def activate_job(self):
        """Aktiviraj job(ove)"""
        selection = self.jobs_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select one or more jobs to activate.")
            return
        
        activated_count = 0
        for item in selection:
            job_id = int(self.jobs_tree.item(item, "tags")[0])
            job = self.job_manager.get_job_by_id(job_id)
            if job:
                job.active = True
                self.job_manager.update_job(job.id, job)
                activated_count += 1
        
        if activated_count > 0:
            self.refresh_jobs_list()
            messagebox.showinfo("Success", f"Activated {activated_count} job(s).")
    
    def deactivate_job(self):
        """Deaktiviraj job(ove)"""
        selection = self.jobs_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select one or more jobs to deactivate.")
            return
        
        deactivated_count = 0
        for item in selection:
            job_id = int(self.jobs_tree.item(item, "tags")[0])
            job = self.job_manager.get_job_by_id(job_id)
            if job:
                job.active = False
                self.job_manager.update_job(job.id, job)
                deactivated_count += 1
        
        if deactivated_count > 0:
            self.refresh_jobs_list()
            messagebox.showinfo("Success", f"Deactivated {deactivated_count} job(s).")
    
    def delete_job(self):
        """Obriši job(ove)"""
        selection = self.jobs_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select one or more jobs to delete.")
            return
        
        # Get job names for confirmation
        job_names = []
        jobs_to_delete = []
        for item in selection:
            job_id = int(self.jobs_tree.item(item, "tags")[0])
            job = self.job_manager.get_job_by_id(job_id)
            if job:
                job_names.append(job.name)
                jobs_to_delete.append(job)
        
        # Confirm deletion
        if len(jobs_to_delete) == 1:
            confirm_msg = f"Are you sure you want to delete job '{jobs_to_delete[0].name}'?"
        else:
            confirm_msg = f"Are you sure you want to delete {len(jobs_to_delete)} jobs?\n\n" + "\n".join(job_names)
        
        if messagebox.askyesno("Confirm Delete", confirm_msg):
            deleted_count = 0
            for job in jobs_to_delete:
                self.job_manager.delete_job(job.id)
                deleted_count += 1
            
            self.refresh_jobs_list()
            messagebox.showinfo("Success", f"Deleted {deleted_count} job(s).")
    
    def open_destination_folder(self):
        """Otvori destination folder za odabrani job"""
        selection = self.jobs_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a job to open its destination folder.")
            return
        
        if len(selection) > 1:
            messagebox.showwarning("Warning", "Please select only one job to open its destination folder.")
            return
        
        # Get selected job
        item = selection[0]
        tags = self.jobs_tree.item(item, "tags")
        if not tags:
            messagebox.showerror("Error", "Could not identify selected job.")
            return
        
        job_id = int(tags[0])  # Job ID is stored in first tag
        job = self.job_manager.get_job_by_id(job_id)
        
        if not job:
            messagebox.showerror("Error", "Selected job not found.")
            return
        
        dest_path = Path(job.dest_path)
        
        # Check if destination exists
        if not dest_path.exists():
            if messagebox.askyesno("Create Folder", 
                                 f"Destination folder doesn't exist:\n{dest_path}\n\nDo you want to create it?"):
                try:
                    dest_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create folder:\n{e}")
                    return
            else:
                return
        
        # Open folder in file explorer
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                # Use os.startfile for Windows - more reliable
                import os
                os.startfile(str(dest_path))
            elif system == "Darwin":  # macOS
                subprocess.run(['open', str(dest_path)], check=False)
            else:  # Linux
                subprocess.run(['xdg-open', str(dest_path)], check=False)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder:\n{dest_path}\n\nError: {e}")
    
    def run_job_manual(self):
        """Pokreni job(ove) ručno"""
        selection = self.jobs_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select one or more jobs to run.")
            return
        
        jobs_to_run = []
        running_jobs = []
        
        # Check which jobs can be run
        for item in selection:
            job_id = int(self.jobs_tree.item(item, "tags")[0])
            job = self.job_manager.get_job_by_id(job_id)
            if job:
                if job.running:
                    running_jobs.append(job.name)
                else:
                    jobs_to_run.append(job)
        
        # Show warning for already running jobs
        if running_jobs:
            messagebox.showwarning("Warning", f"The following jobs are already running:\n" + "\n".join(running_jobs))
        
        # Run the jobs that can be run
        if jobs_to_run:
            for job in jobs_to_run:
                self.logger.info(f"[Manual] Starting job '{job.name}' manually")
                print(f"Manual run: Starting job '{job.name}' (ID: {job.id})")
                # Run job in separate thread
                thread = threading.Thread(target=self.execute_job, args=(job, True))
                thread.daemon = True
                thread.start()
            
            messagebox.showinfo("Success", f"Started {len(jobs_to_run)} job(s).")
    
    def should_exclude_path(self, path, exclude_patterns):
        """Provjeri treba li putanju isključiti na osnovu exclude patterns"""
        if not exclude_patterns:
            return False
        
        patterns = [p.strip() for p in exclude_patterns.split(',') if p.strip()]
        path_str = str(path)
        path_name = path.name
        
        for pattern in patterns:
            # Exact match
            if path_name == pattern:
                return True
            
            # Wildcard match
            if '*' in pattern:
                import fnmatch
                if fnmatch.fnmatch(path_name, pattern):
                    return True
            
            # Directory anywhere in path
            if pattern in path_str:
                return True
        
        return False
    
    def show_notification(self, title, message, timeout=5):
        """Prikaži desktop notifikaciju"""
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                app_name="SyncBackup v1.3",
                timeout=timeout,
                app_icon=None  # Možemo dodati ikonu kasnije
            )
        except ImportError:
            print(f"Notification (plyer not available): {title} - {message}")
        except Exception as e:
            print(f"Notification error: {e}")
    
    def notify_job_result(self, job, status, message="", files_processed=0, duration=0):
        """Pošalji notifikaciju ovisno o statusu job-a"""
        if not job.enable_notifications:
            return
        
        # Check notification mode
        notification_mode = self.db_manager.get_setting('notification_mode', 'batch')
        
        if notification_mode == 'disabled':
            return
        
        if notification_mode == 'batch':
            # Add to notification queue for batch processing
            self.db_manager.add_notification_to_queue(
                job.id, job.name, status, message, files_processed, duration
            )
        else:
            # Immediate mode - show notification right away
            if status == "success":
                self.show_notification(
                    title="✅ Backup Completed",
                    message=f"Job: {job.name}\n{files_processed} files processed\nDuration: {duration:.1f}s"
                )
            elif status == "error":
                self.show_notification(
                    title="❌ Backup Failed",
                    message=f"Job: {job.name}\nError: {message[:50]}{'...' if len(message) > 50 else ''}"
                )
            elif status == "skipped":
                self.show_notification(
                    title="⏸️ Backup Skipped",
                    message=f"Job: {job.name}\nNo changes detected"
                )
    
    def copy_with_exclusions(self, source, destination, exclude_patterns):
        """Kopira direktorij s isključivanjem određenih pattern-a"""
        import os
        import shutil
        
        def should_copy(path):
            return not self.should_exclude_path(Path(path), exclude_patterns)
        
        # Create destination directory
        destination.mkdir(parents=True, exist_ok=True)
        
        # Walk through source directory
        for root, dirs, files in os.walk(source):
            root_path = Path(root)
            
            # Filter directories
            dirs[:] = [d for d in dirs if should_copy(root_path / d)]
            
            # Create corresponding directory structure
            rel_path = root_path.relative_to(source)
            dest_dir = destination / rel_path
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy files
            for file in files:
                file_path = root_path / file
                if should_copy(file_path):
                    dest_file = dest_dir / file
                    try:
                        shutil.copy2(file_path, dest_file)
                    except Exception as e:
                        print(f"Warning: Could not copy {file_path}: {e}")
    
    def create_zip_backup(self, source, destination_zip, exclude_patterns):
        """Kreira ZIP backup s isključivanjem određenih pattern-a"""
        import zipfile
        import os
        
        with zipfile.ZipFile(destination_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for root, dirs, files in os.walk(source):
                root_path = Path(root)
                
                # Filter directories
                dirs[:] = [d for d in dirs if not self.should_exclude_path(root_path / d, exclude_patterns)]
                
                # Add files to ZIP
                for file in files:
                    file_path = root_path / file
                    if not self.should_exclude_path(file_path, exclude_patterns):
                        try:
                            # Calculate relative path for ZIP
                            arcname = os.path.relpath(file_path, source)
                            zipf.write(file_path, arcname)
                        except Exception as e:
                            print(f"Warning: Could not add {file_path} to ZIP: {e}")
    
    def execute_job(self, job, force=False):
        """Izvrši job"""
        job.running = True
        self.root.after(0, self.refresh_jobs_list)  # Update GUI in main thread
        
        start_time = time.time()
        try:
            self.logger.info(f"[Job: {job.name}] Job started (force={force})")
            self.db_manager.add_job_log(job.id, "started", f"Job started (force={force})")
            print(f"Execute job: {job.name} (Type: {job.job_type}, Force: {force})")
            
            if job.job_type == "Simple":
                files_processed = self.execute_simple_job(job, force)
            elif job.job_type == "Incremental":
                files_processed = self.execute_incremental_job(job, force)
            else:
                self.logger.error(f"[Job: {job.name}] Unknown job type: {job.job_type}")
                self.db_manager.add_job_log(job.id, "error", f"Unknown job type: {job.job_type}")
                return
            
            job.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.calculate_next_run(job)
            self.job_manager.save_jobs()  # Save after updating last_run and next_run
            
            # Update GUI in main thread
            self.root.after(0, self.refresh_jobs_list)
            
            duration = time.time() - start_time
            self.logger.info(f"[Job: {job.name}] Job completed successfully")
            self.db_manager.add_job_log(job.id, "completed", "Job completed successfully", 
                                      duration_seconds=duration, files_processed=files_processed)
            print(f"Job completed: {job.name}")
            
            # Send success notification
            self.notify_job_result(job, "success", files_processed=files_processed, duration=duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"[Job: {job.name}] Job failed: {e}")
            self.db_manager.add_job_log(job.id, "error", f"Job failed: {e}", 
                                      duration_seconds=duration)
            print(f"Job failed: {job.name} - {e}")
            
            # Send error notification
            self.notify_job_result(job, "error", message=str(e), duration=duration)
        finally:
            job.running = False
            self.root.after(0, self.refresh_jobs_list)  # Update GUI in main thread
    
    def execute_simple_job(self, job, force=False):
        """Izvrši Simple job"""
        source_path = Path(job.source_path)
        dest_base = Path(job.dest_path)
        files_processed = 0
        
        # Check for changes (skip if force=True)
        if force or self.has_changes_simple(job):
            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = source_path.name
            backup_name = f"{folder_name}_{timestamp}"
            
            if job.compress_backup:
                # Create ZIP backup
                backup_path = dest_base / f"{backup_name}.zip"
                self.create_zip_backup(source_path, backup_path, job.exclude_patterns)
                # Count files in source (approximation for ZIP)
                files_processed = len([f for f in source_path.rglob('*') if f.is_file() and not self.should_exclude_path(f, job.exclude_patterns)])
            else:
                # Create folder backup
                backup_path = dest_base / backup_name
                self.copy_with_exclusions(source_path, backup_path, job.exclude_patterns)
                # Count files processed
                files_processed = len(list(backup_path.rglob('*')))
            
            # Update last backup hash
            self.update_backup_hash(job, source_path)
            
            # Track backup file in database
            self.db_manager.add_backup_file(
                job.id, 
                str(backup_path), 
                'simple_backup',
                datetime.now().isoformat(),
                self.get_folder_size(backup_path)
            )
            
            if force:
                self.logger.info(f"[Job: {job.name}] Created forced backup: {backup_name}")
            else:
                self.logger.info(f"[Job: {job.name}] Created backup: {backup_name}")
        else:
            self.logger.info(f"[Job: {job.name}] No changes detected, skipping backup")
            self.db_manager.add_job_log(job.id, "skipped", "No changes detected, skipping backup")
            
            # Send skipped notification
            self.notify_job_result(job, "skipped")
        
        # Apply retention policies
        self.apply_retention_policies(job)
        return files_processed
    
    def execute_incremental_job(self, job, force=False):
        """Izvrši Incremental job"""
        source_path = Path(job.source_path)
        dest_base = Path(job.dest_path)
        sync_path = dest_base / source_path.name
        files_processed = 0
        
        # Create sync directory if it doesn't exist
        sync_path.mkdir(parents=True, exist_ok=True)
        
        # First run - create initial backup
        if not self.has_incremental_backup(job):
            # Remove existing sync_path if it exists
            if sync_path.exists():
                shutil.rmtree(sync_path)
            self.copy_with_exclusions(source_path, sync_path, job.exclude_patterns)
            files_processed = len(list(sync_path.rglob('*')))
            self.logger.info(f"[Job: {job.name}] Created initial incremental backup")
            self.mark_incremental_backup(job)
        else:
            # Incremental sync
            files_processed = self.sync_incremental(source_path, sync_path, job.preserve_deleted, job.exclude_patterns)
            self.logger.info(f"[Job: {job.name}] Incremental sync completed")
            # Update incremental backup hash after sync
            self.mark_incremental_backup(job)
        
        # Create snapshot if needed
        if job.create_snapshots and self.should_create_snapshot(job):
            self.create_incremental_snapshot(job, sync_path)
        
        # Apply retention policies
        self.apply_retention_policies(job)
        return files_processed
    
    def has_changes_simple(self, job):
        """Provjeri ima li promjena za Simple job"""
        source_path = Path(job.source_path)
        if not source_path.exists():
            return False
        
        # Get the most recent modification time of any file in the source directory
        max_mtime = 0
        try:
            for file_path in source_path.rglob('*'):
                if file_path.is_file():
                    max_mtime = max(max_mtime, file_path.stat().st_mtime)
        except:
            # If we can't read files, fall back to directory mtime
            max_mtime = source_path.stat().st_mtime
        
        # Check if we have a record of last backup
        hash_record = self.db_manager.get_backup_hash(job.id, 'simple')
        if hash_record:
            last_mtime = hash_record.get('mtime', 0)
            return max_mtime > last_mtime
        
        return True  # First run or no hash record
    
    def update_backup_hash(self, job, source_path):
        """Ažuriraj hash za Simple job"""
        # Get the most recent modification time of any file in the source directory
        max_mtime = 0
        try:
            for file_path in source_path.rglob('*'):
                if file_path.is_file():
                    max_mtime = max(max_mtime, file_path.stat().st_mtime)
        except:
            # If we can't read files, fall back to directory mtime
            max_mtime = source_path.stat().st_mtime
        
        self.db_manager.update_backup_hash(job.id, 'simple', max_mtime)
    
    def has_incremental_backup(self, job):
        """Provjeri ima li incremental backup"""
        hash_record = self.db_manager.get_backup_hash(job.id, 'incremental')
        return hash_record is not None
    
    def mark_incremental_backup(self, job):
        """Označi da je incremental backup kreiran"""
        # Use current timestamp as mtime for incremental jobs
        self.db_manager.update_backup_hash(job.id, 'incremental', time.time())
    
    def sync_incremental(self, source, dest, preserve_deleted, exclude_patterns=""):
        """Sinkroniziraj incremental"""
        files_processed = 0
        
        # Copy new and modified files
        for root, dirs, files in os.walk(source):
            root_path = Path(root)
            
            # Filter directories based on exclude patterns
            dirs[:] = [d for d in dirs if not self.should_exclude_path(root_path / d, exclude_patterns)]
            
            rel_path = os.path.relpath(root, source)
            dest_dir = dest / rel_path if rel_path != '.' else dest
            
            # Create directories
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy files
            for file in files:
                src_file = Path(root) / file
                
                # Skip excluded files
                if self.should_exclude_path(src_file, exclude_patterns):
                    continue
                
                dst_file = dest_dir / file
                
                # Copy if source is newer or destination doesn't exist
                if not dst_file.exists() or src_file.stat().st_mtime > dst_file.stat().st_mtime:
                    shutil.copy2(src_file, dst_file)
                    files_processed += 1
        
        # Remove deleted files if not preserving
        if not preserve_deleted:
            for root, dirs, files in os.walk(dest):
                rel_path = os.path.relpath(root, dest)
                src_dir = source / rel_path if rel_path != '.' else source
                
                for file in files:
                    dst_file = Path(root) / file
                    src_file = src_dir / file
                    
                    if not src_file.exists():
                        dst_file.unlink()
                        files_processed += 1
        
        return files_processed
    
    def should_create_snapshot(self, job):
        """Provjeri treba li kreirati snapshot"""
        hash_file = Path("backup_hashes.json")
        if not hash_file.exists():
            return True
        
        try:
            with open(hash_file, 'r') as f:
                hashes = json.load(f)
                job_key = f"incremental_{job.id}"
                if job_key in hashes:
                    last_snapshot = hashes[job_key].get('last_snapshot')
                    if last_snapshot:
                        last_time = datetime.fromisoformat(last_snapshot)
                        interval_hours = job.snapshot_interval
                        return datetime.now() - last_time >= timedelta(hours=interval_hours)
                    return True
        except:
            pass
        
        return True
    
    def create_incremental_snapshot(self, job, sync_path):
        """Kreiraj incremental snapshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = sync_path.name
        snapshot_name = f"{folder_name}_INCREMENTAL_{timestamp}"
        snapshot_path = sync_path.parent / snapshot_name
        
        # Copy sync directory to snapshot
        shutil.copytree(sync_path, snapshot_path)
        
        # Track snapshot in database
        self.db_manager.add_backup_file(
            job.id, 
            str(snapshot_path), 
            'incremental_snapshot',
            datetime.now().isoformat(),
            self.get_folder_size(snapshot_path)
        )
        
        self.logger.info(f"[Job: {job.name}] Created incremental snapshot: {snapshot_name}")
    
    def get_folder_size(self, folder_path):
        """Get total size of folder in bytes"""
        total_size = 0
        try:
            for file_path in Path(folder_path).rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except:
            pass
        return total_size
    
    def apply_retention_policies(self, job):
        """Apply retention policies for job"""
        try:
            policies = self.db_manager.get_retention_policies(job.id)
            
            for policy in policies:
                policy_type = policy['policy_type']
                policy_value = policy['policy_value']
                
                deleted_count = self.db_manager.cleanup_old_backups(job.id, policy_type, policy_value)
                
                if deleted_count > 0:
                    self.logger.info(f"[Job: {job.name}] Retention policy '{policy_type}' deleted {deleted_count} old backups")
                    
                    # Delete actual files from filesystem
                    self.delete_backup_files_from_fs(job.id, policy_type, policy_value)
                    
        except Exception as e:
            self.logger.error(f"[Job: {job.name}] Error applying retention policies: {e}")
    
    def delete_backup_files_from_fs(self, job_id, policy_type, policy_value):
        """Delete backup files from filesystem based on retention policy"""
        try:
            # Get files to delete from database
            backup_files = self.db_manager.get_backup_files(job_id)
            
            if policy_type == 'keep_count':
                # Keep only the most recent N files
                files_to_delete = backup_files[policy_value:]
            elif policy_type == 'keep_days':
                # Delete files older than N days
                cutoff_date = datetime.now() - timedelta(days=policy_value)
                files_to_delete = [f for f in backup_files 
                                 if datetime.fromisoformat(f['created_at']) < cutoff_date]
            elif policy_type == 'keep_size':
                # Delete files until total size is under limit
                total_size = 0
                files_to_delete = []
                for file_info in reversed(backup_files):  # Start from oldest
                    if total_size + file_info['file_size'] > policy_value * 1024 * 1024:
                        files_to_delete.append(file_info)
                    else:
                        total_size += file_info['file_size']
            
            # Delete files from filesystem
            for file_info in files_to_delete:
                try:
                    file_path = Path(file_info['file_path'])
                    if file_path.exists():
                        if file_path.is_dir():
                            shutil.rmtree(file_path)
                        else:
                            file_path.unlink()
                        self.logger.info(f"[Job: {job_id}] Deleted old backup: {file_path}")
                except Exception as e:
                    self.logger.error(f"[Job: {job_id}] Error deleting {file_info['file_path']}: {e}")
                    
        except Exception as e:
            self.logger.error(f"[Job: {job_id}] Error deleting backup files from filesystem: {e}")
    
    def start_scheduler(self):
        """Pokreni scheduler"""
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self.scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
    
    def scheduler_loop(self):
        """Scheduler loop"""
        while self.scheduler_running:
            try:
                # Check all active jobs
                for job in self.job_manager.jobs:
                    if job.active and not job.running:
                        # Update next_run if it's in the past
                        if job.next_run:
                            try:
                                next_run = datetime.strptime(job.next_run, "%Y-%m-%d %H:%M:%S")
                                if next_run <= datetime.now():
                                    self.calculate_next_run(job)
                                    self.job_manager.save_jobs()
                                    # Update GUI in main thread
                                    self.root.after(0, self.refresh_jobs_list)
                            except:
                                # If parsing fails, recalculate
                                self.calculate_next_run(job)
                                self.job_manager.save_jobs()
                                # Update GUI in main thread
                                self.root.after(0, self.refresh_jobs_list)
                        
                        if self.should_run_job(job):
                            # Run job in background
                            thread = threading.Thread(target=self.execute_job, args=(job,))
                            thread.daemon = True
                            thread.start()
                
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    def should_run_job(self, job):
        """Provjeri treba li pokrenuti job"""
        now = datetime.now()
        
        if job.schedule_type == "Daily at specific time":
            try:
                schedule_time = datetime.strptime(job.schedule_value, "%H:%M").time()
                # Check if it's time to run today
                if now.time() >= schedule_time:
                    if job.last_run:
                        last_run = datetime.strptime(job.last_run, "%Y-%m-%d %H:%M:%S")
                        # Run if last run was before today
                        if last_run.date() < now.date():
                            return True
                    else:
                        # First run
                        return True
                # Also check if next_run is in the past (for jobs that missed their time)
                elif job.next_run:
                    next_run = datetime.strptime(job.next_run, "%Y-%m-%d %H:%M:%S")
                    if next_run <= now:
                        return True
            except:
                pass
        
        elif job.schedule_type == "Every X minutes":
            try:
                interval_minutes = int(job.schedule_value)
                if job.last_run:
                    last_run = datetime.strptime(job.last_run, "%Y-%m-%d %H:%M:%S")
                    time_diff = now - last_run
                    if time_diff.total_seconds() >= interval_minutes * 60:
                        return True
                else:
                    return True  # First run
                # Also check if next_run is in the past
                if job.next_run:
                    next_run = datetime.strptime(job.next_run, "%Y-%m-%d %H:%M:%S")
                    if next_run <= now:
                        return True
            except:
                pass
        
        elif job.schedule_type == "Every X hours":
            try:
                interval_hours = int(job.schedule_value)
                if job.last_run:
                    last_run = datetime.strptime(job.last_run, "%Y-%m-%d %H:%M:%S")
                    time_diff = now - last_run
                    if time_diff.total_seconds() >= interval_hours * 3600:
                        return True
                else:
                    return True  # First run
                # Also check if next_run is in the past
                if job.next_run:
                    next_run = datetime.strptime(job.next_run, "%Y-%m-%d %H:%M:%S")
                    if next_run <= now:
                        return True
            except:
                pass
        
        # Add other schedule types as needed
        return False
    
    def calculate_next_run(self, job):
        """Izračunaj sljedeće pokretanje job-a"""
        now = datetime.now()
        
        if job.schedule_type == "Every X minutes":
            try:
                interval_minutes = int(job.schedule_value)
                next_run = now + timedelta(minutes=interval_minutes)
                job.next_run = next_run.strftime("%Y-%m-%d %H:%M:%S")
            except:
                job.next_run = None
        
        elif job.schedule_type == "Every X hours":
            try:
                interval_hours = int(job.schedule_value)
                next_run = now + timedelta(hours=interval_hours)
                job.next_run = next_run.strftime("%Y-%m-%d %H:%M:%S")
            except:
                job.next_run = None
        
        elif job.schedule_type == "Daily at specific time":
            try:
                schedule_time = datetime.strptime(job.schedule_value, "%H:%M").time()
                next_run = datetime.combine(now.date(), schedule_time)
                if next_run <= now:
                    next_run += timedelta(days=1)
                job.next_run = next_run.strftime("%Y-%m-%d %H:%M:%S")
            except:
                job.next_run = None
        
        else:
            job.next_run = None
    
    def start_notification_processor(self):
        """Start notification batch processor"""
        self.notification_running = True
        self.notification_thread = threading.Thread(target=self.notification_processor_loop)
        self.notification_thread.daemon = True
        self.notification_thread.start()
    
    def notification_processor_loop(self):
        """Notification batch processor loop"""
        while self.notification_running:
            try:
                # Get batch interval from settings
                batch_interval = int(self.db_manager.get_setting('notification_batch_interval', '300'))
                
                # Wait for the batch interval
                time.sleep(batch_interval)
                
                # Check if batch mode is enabled
                notification_mode = self.db_manager.get_setting('notification_mode', 'batch')
                if notification_mode != 'batch':
                    continue
                
                # Get pending notifications
                pending_notifications = self.db_manager.get_pending_notifications()
                
                if pending_notifications:
                    # Process batch notification
                    self.send_batch_notification(pending_notifications)
                    
                    # Mark notifications as sent
                    notification_ids = [n['id'] for n in pending_notifications]
                    self.db_manager.mark_notifications_as_sent(notification_ids)
                    
                    # Cleanup old notifications (older than 7 days)
                    self.db_manager.cleanup_old_notifications(7)
                    
            except Exception as e:
                self.logger.error(f"Notification processor error: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def send_batch_notification(self, notifications):
        """Send a batch notification summarizing multiple job results"""
        if not notifications:
            return
        
        # Count by status
        success_count = sum(1 for n in notifications if n['status'] == 'success')
        error_count = sum(1 for n in notifications if n['status'] == 'error')
        skipped_count = sum(1 for n in notifications if n['status'] == 'skipped')
        
        # Build summary message
        title = f"📊 Backup Summary ({len(notifications)} jobs)"
        
        message_parts = []
        if success_count > 0:
            message_parts.append(f"✅ {success_count} completed")
        if error_count > 0:
            message_parts.append(f"❌ {error_count} failed")
        if skipped_count > 0:
            message_parts.append(f"⏸️ {skipped_count} skipped")
        
        message = "\n".join(message_parts)
        
        # Add details for failed jobs
        if error_count > 0:
            failed_jobs = [n['job_name'] for n in notifications if n['status'] == 'error']
            message += f"\n\nFailed: {', '.join(failed_jobs[:3])}"
            if len(failed_jobs) > 3:
                message += f" (+{len(failed_jobs) - 3} more)"
        
        # Show the batch notification
        self.show_notification(title, message, timeout=10)
    
    def refresh_log(self):
        """Osvježi log viewer"""
        try:
            # Get logs from database
            logs = self.db_manager.get_job_logs(limit=1000)
            
            # Clear and populate log text
            self.log_text.delete(1.0, tk.END)
            
            if not logs:
                self.log_text.insert(1.0, "No logs found in database.\n")
                return
            
            # Format logs for display
            for log in reversed(logs):  # Show newest first
                timestamp = log['execution_time']
                job_name = log.get('job_name', 'Unknown')
                status = log['status']
                message = log.get('message', '')
                duration = log.get('duration_seconds') or 0
                files_processed = log.get('files_processed') or 0
                
                # Format log entry
                log_entry = f"[{timestamp}] [{status.upper()}] [Job: {job_name}] {message}"
                if duration and duration > 0:
                    log_entry += f" (Duration: {duration:.2f}s"
                if files_processed and files_processed > 0:
                    log_entry += f", Files: {files_processed}"
                if (duration and duration > 0) or (files_processed and files_processed > 0):
                    log_entry += ")"
                log_entry += "\n"
                
                self.log_text.insert(1.0, log_entry)
            
            self.log_text.see(tk.END)
        except Exception as e:
            self.log_text.insert(tk.END, f"Error reading logs from database: {e}\n")
    
    def clear_log(self):
        """Obriši log iz baze"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all logs from database?"):
            try:
                # Clear logs from database
                with sqlite3.connect(self.db_manager.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM job_logs")
                    conn.commit()
                self.refresh_log()
                messagebox.showinfo("Success", "All logs cleared from database.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear logs: {e}")
    
    def save_log(self):
        """Spremi log kao fajl"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                # Get logs from database
                logs = self.db_manager.get_job_logs(limit=10000)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    if not logs:
                        f.write("No logs found in database.\n")
                    else:
                        for log in logs:
                            timestamp = log['execution_time']
                            job_name = log.get('job_name', 'Unknown')
                            status = log['status']
                            message = log.get('message', '')
                            duration = log.get('duration_seconds', 0)
                            files_processed = log.get('files_processed', 0)
                            
                            # Format log entry
                            log_entry = f"[{timestamp}] [{status.upper()}] [Job: {job_name}] {message}"
                            if duration > 0:
                                log_entry += f" (Duration: {duration:.2f}s"
                            if files_processed > 0:
                                log_entry += f", Files: {files_processed}"
                            if duration > 0 or files_processed > 0:
                                log_entry += ")"
                            log_entry += "\n"
                            
                            f.write(log_entry)
                
                messagebox.showinfo("Success", f"Log saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log: {e}")
    
    def filter_log(self, event=None):
        """Filtriraj log"""
        try:
            # Get selected filter
            filter_value = self.log_filter.get()
            
            # Get logs from database
            logs = self.db_manager.get_job_logs(limit=1000)
            
            # Clear and populate log text
            self.log_text.delete(1.0, tk.END)
            
            if not logs:
                self.log_text.insert(1.0, "No logs found in database.\n")
                return
            
            # Filter logs based on selection
            filtered_logs = []
            for log in logs:
                status = log['status']
                
                if filter_value == "All":
                    filtered_logs.append(log)
                elif filter_value == "Errors Only" and status == "error":
                    filtered_logs.append(log)
                elif filter_value == "Info Only" and status in ["started", "completed", "skipped"]:
                    filtered_logs.append(log)
                elif filter_value == "Skipped Only" and status == "skipped":
                    filtered_logs.append(log)
                elif filter_value == "Completed Only" and status == "completed":
                    filtered_logs.append(log)
            
            # Format filtered logs for display
            for log in reversed(filtered_logs):  # Show newest first
                timestamp = log['execution_time']
                job_name = log.get('job_name', 'Unknown')
                status = log['status']
                message = log.get('message', '')
                duration = log.get('duration_seconds') or 0
                files_processed = log.get('files_processed') or 0
                
                # Format log entry
                log_entry = f"[{timestamp}] [{status.upper()}] [Job: {job_name}] {message}"
                if duration and duration > 0:
                    log_entry += f" (Duration: {duration:.2f}s"
                if files_processed and files_processed > 0:
                    log_entry += f", Files: {files_processed}"
                if (duration and duration > 0) or (files_processed and files_processed > 0):
                    log_entry += ")"
                log_entry += "\n"
                
                self.log_text.insert(1.0, log_entry)
            
            self.log_text.see(tk.END)
        except Exception as e:
            self.log_text.insert(tk.END, f"Error filtering logs: {e}\n")
    
    def on_close(self):
        """Handle window close button"""
        if messagebox.askyesno(self._("messages.confirm"), self._("messages.quit_confirm")):
            self.scheduler_running = False
            self.notification_running = False
            if self.tray_icon:
                self.tray_icon.stop()
            self.root.quit()
    
    def on_minimize(self, event=None):
        """Handle window minimize"""
        if self.tray_icon:
            self.tray_icon.minimize_to_tray()
    
    def run(self):
        """Pokreni aplikaciju"""
        # Bind minimize event
        self.root.bind("<Unmap>", lambda e: self.on_minimize() if self.root.state() == "iconic" else None)
        
        try:
            self.root.mainloop()
        finally:
            self.scheduler_running = False
            self.notification_running = False
            if self.tray_icon:
                self.tray_icon.stop()

if __name__ == "__main__":
    try:
        with SingleInstance():
            app = SyncBackupApp()
            app.run()
    except Exception as e:
        print(f"Error: {e}")
        messagebox.showerror("SyncBackup", str(e))
        sys.exit(1)
