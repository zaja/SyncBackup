"""
Database manager for SyncBackup v1.1 application

Autor: Goran Zajec
Web stranica: https://svejedobro.hr
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

class DatabaseManager:
    """SQLite database manager for jobs and backup hashes"""
    
    def __init__(self, db_path: str = "app/sync_backup.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    job_type TEXT NOT NULL CHECK (job_type IN ('Simple', 'Incremental')),
                    source_path TEXT NOT NULL,
                    dest_path TEXT NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    schedule_type TEXT NOT NULL,
                    schedule_value TEXT NOT NULL,
                    preserve_deleted BOOLEAN DEFAULT 0,
                    create_snapshots BOOLEAN DEFAULT 0,
                    snapshot_interval INTEGER DEFAULT 24,
                    last_run DATETIME,
                    next_run DATETIME,
                    running BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Backup hashes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_hashes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    hash_type TEXT NOT NULL CHECK (hash_type IN ('simple', 'incremental')),
                    mtime REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
                )
            """)
            
            # Job execution logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    execution_time DATETIME NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('started', 'completed', 'success', 'error', 'skipped')),
                    message TEXT,
                    duration_seconds REAL,
                    files_processed INTEGER DEFAULT 0,
                    FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
                )
            """)
            
            # File retention policies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS retention_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    policy_type TEXT NOT NULL CHECK (policy_type IN ('keep_count', 'keep_days', 'keep_size')),
                    policy_value INTEGER NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
                )
            """)
            
            # Backup files tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL CHECK (file_type IN ('simple_backup', 'incremental_snapshot')),
                    created_at DATETIME NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_next_run ON jobs(next_run)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_backup_hashes_job_id ON backup_hashes(job_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_logs_job_id ON job_logs(job_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_logs_execution_time ON job_logs(execution_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_retention_policies_job_id ON retention_policies(job_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_backup_files_job_id ON backup_files(job_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_backup_files_created_at ON backup_files(created_at)")
            
            conn.commit()
    
    def migrate_from_json(self):
        """Migrate existing data from JSON files to SQLite"""
        # Check if jobs table already has data
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs")
            count = cursor.fetchone()[0]
            if count > 0:
                print("Jobs already exist in database, skipping migration")
                return
        
        # Migrate jobs from jobs.json
        jobs_file = Path("jobs.json")
        if jobs_file.exists():
            try:
                with open(jobs_file, 'r') as f:
                    jobs_data = json.load(f)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    for job_data in jobs_data:
                        cursor.execute("""
                            INSERT OR IGNORE INTO jobs (
                                id, name, job_type, source_path, dest_path, active,
                                schedule_type, schedule_value, preserve_deleted,
                                create_snapshots, snapshot_interval, last_run,
                                next_run, running
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            job_data.get('id'),
                            job_data.get('name'),
                            job_data.get('job_type'),
                            job_data.get('source_path'),
                            job_data.get('dest_path'),
                            job_data.get('active', True),
                            job_data.get('schedule_type'),
                            job_data.get('schedule_value'),
                            job_data.get('preserve_deleted', False),
                            job_data.get('create_snapshots', False),
                            job_data.get('snapshot_interval', 24),
                            job_data.get('last_run'),
                            job_data.get('next_run'),
                            job_data.get('running', False)
                        ))
                    
                    conn.commit()
                    print(f"Migrated {len(jobs_data)} jobs from jobs.json")
                    
            except Exception as e:
                print(f"Error migrating jobs from JSON: {e}")
        
        # Check if backup_hashes table already has data
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM backup_hashes")
            count = cursor.fetchone()[0]
            if count > 0:
                print("Backup hashes already exist in database, skipping migration")
                return
        
        # Migrate backup hashes from backup_hashes.json
        hashes_file = Path("backup_hashes.json")
        if hashes_file.exists():
            try:
                with open(hashes_file, 'r') as f:
                    hashes_data = json.load(f)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    for hash_key, hash_data in hashes_data.items():
                        # Parse hash_key format: "simple_1" or "incremental_1"
                        parts = hash_key.split('_')
                        if len(parts) >= 2:
                            hash_type = parts[0]
                            job_id = int(parts[1])
                            
                            cursor.execute("""
                                INSERT OR IGNORE INTO backup_hashes (job_id, hash_type, mtime, timestamp)
                                VALUES (?, ?, ?, ?)
                            """, (
                                job_id,
                                hash_type,
                                hash_data.get('mtime', 0),
                                hash_data.get('timestamp', datetime.now().isoformat())
                            ))
                    
                    conn.commit()
                    print(f"Migrated {len(hashes_data)} backup hashes from backup_hashes.json")
                    
            except Exception as e:
                print(f"Error migrating backup hashes from JSON: {e}")
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM jobs ORDER BY id")
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            
            return dict(row) if row else None
    
    def add_job(self, job_data: Dict[str, Any]) -> int:
        """Add new job and return its ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO jobs (
                    name, job_type, source_path, dest_path, active,
                    schedule_type, schedule_value, preserve_deleted,
                    create_snapshots, snapshot_interval, last_run,
                    next_run, running
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_data.get('name'),
                job_data.get('job_type'),
                job_data.get('source_path'),
                job_data.get('dest_path'),
                job_data.get('active', True),
                job_data.get('schedule_type'),
                job_data.get('schedule_value'),
                job_data.get('preserve_deleted', False),
                job_data.get('create_snapshots', False),
                job_data.get('snapshot_interval', 24),
                job_data.get('last_run'),
                job_data.get('next_run'),
                job_data.get('running', False)
            ))
            
            job_id = cursor.lastrowid
            conn.commit()
            return job_id
    
    def update_job(self, job_id: int, job_data: Dict[str, Any]):
        """Update existing job"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE jobs SET
                    name = ?, job_type = ?, source_path = ?, dest_path = ?,
                    active = ?, schedule_type = ?, schedule_value = ?,
                    preserve_deleted = ?, create_snapshots = ?, snapshot_interval = ?,
                    last_run = ?, next_run = ?, running = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                job_data.get('name'),
                job_data.get('job_type'),
                job_data.get('source_path'),
                job_data.get('dest_path'),
                job_data.get('active', True),
                job_data.get('schedule_type'),
                job_data.get('schedule_value'),
                job_data.get('preserve_deleted', False),
                job_data.get('create_snapshots', False),
                job_data.get('snapshot_interval', 24),
                job_data.get('last_run'),
                job_data.get('next_run'),
                job_data.get('running', False),
                job_id
            ))
            
            conn.commit()
    
    def delete_job(self, job_id: int):
        """Delete job and related data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Delete job (cascade will handle related records)
            cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            conn.commit()
    
    def get_backup_hash(self, job_id: int, hash_type: str) -> Optional[Dict[str, Any]]:
        """Get backup hash for job"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM backup_hashes 
                WHERE job_id = ? AND hash_type = ?
                ORDER BY timestamp DESC LIMIT 1
            """, (job_id, hash_type))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_backup_hash(self, job_id: int, hash_type: str, mtime: float):
        """Update backup hash for job"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO backup_hashes (job_id, hash_type, mtime, timestamp)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (job_id, hash_type, mtime))
            
            conn.commit()
    
    def add_job_log(self, job_id: int, status: str, message: str = None, 
                   duration_seconds: float = None, files_processed: int = 0):
        """Add job execution log"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO job_logs (
                    job_id, execution_time, status, message, 
                    duration_seconds, files_processed
                ) VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
            """, (job_id, status, message, duration_seconds, files_processed))
            
            conn.commit()
    
    def get_job_logs(self, job_id: int = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get job execution logs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if job_id:
                cursor.execute("""
                    SELECT jl.*, j.name as job_name
                    FROM job_logs jl
                    JOIN jobs j ON jl.job_id = j.id
                    WHERE jl.job_id = ?
                    ORDER BY jl.execution_time DESC
                    LIMIT ?
                """, (job_id, limit))
            else:
                cursor.execute("""
                    SELECT jl.*, j.name as job_name
                    FROM job_logs jl
                    JOIN jobs j ON jl.job_id = j.id
                    ORDER BY jl.execution_time DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old job logs"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM job_logs 
                WHERE execution_time < datetime('now', '-{} days')
            """.format(days_to_keep))
            
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
    
    # Retention Policy Methods
    def add_retention_policy(self, job_id: int, policy_type: str, policy_value: int, enabled: bool = True):
        """Add retention policy for job"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO retention_policies (job_id, policy_type, policy_value, enabled)
                VALUES (?, ?, ?, ?)
            """, (job_id, policy_type, policy_value, enabled))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_retention_policies(self, job_id: int = None) -> List[Dict[str, Any]]:
        """Get retention policies"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if job_id:
                cursor.execute("""
                    SELECT rp.*, j.name as job_name
                    FROM retention_policies rp
                    JOIN jobs j ON rp.job_id = j.id
                    WHERE rp.job_id = ? AND rp.enabled = 1
                """, (job_id,))
            else:
                cursor.execute("""
                    SELECT rp.*, j.name as job_name
                    FROM retention_policies rp
                    JOIN jobs j ON rp.job_id = j.id
                    WHERE rp.enabled = 1
                """)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def update_retention_policy(self, policy_id: int, policy_type: str = None, 
                               policy_value: int = None, enabled: bool = None):
        """Update retention policy"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if policy_type is not None:
                updates.append("policy_type = ?")
                params.append(policy_type)
            
            if policy_value is not None:
                updates.append("policy_value = ?")
                params.append(policy_value)
            
            if enabled is not None:
                updates.append("enabled = ?")
                params.append(enabled)
            
            if updates:
                params.append(policy_id)
                cursor.execute(f"""
                    UPDATE retention_policies 
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                
                conn.commit()
    
    def delete_retention_policy(self, policy_id: int):
        """Delete retention policy"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM retention_policies WHERE id = ?", (policy_id,))
            conn.commit()
    
    # Backup Files Tracking Methods
    def add_backup_file(self, job_id: int, file_path: str, file_type: str, 
                       created_at: str = None, file_size: int = 0):
        """Add backup file to tracking"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if created_at is None:
                created_at = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO backup_files (job_id, file_path, file_type, created_at, file_size)
                VALUES (?, ?, ?, ?, ?)
            """, (job_id, file_path, file_type, created_at, file_size))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_backup_files(self, job_id: int = None, file_type: str = None) -> List[Dict[str, Any]]:
        """Get backup files"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT bf.*, j.name as job_name
                FROM backup_files bf
                JOIN jobs j ON bf.job_id = j.id
                WHERE 1=1
            """
            params = []
            
            if job_id:
                query += " AND bf.job_id = ?"
                params.append(job_id)
            
            if file_type:
                query += " AND bf.file_type = ?"
                params.append(file_type)
            
            query += " ORDER BY bf.created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def delete_backup_file(self, file_id: int):
        """Delete backup file record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM backup_files WHERE id = ?", (file_id,))
            conn.commit()
    
    def cleanup_old_backups(self, job_id: int, policy_type: str, policy_value: int) -> int:
        """Clean up old backups based on retention policy"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if policy_type == 'keep_count':
                # Keep only the most recent N backups
                cursor.execute("""
                    DELETE FROM backup_files 
                    WHERE job_id = ? AND id NOT IN (
                        SELECT id FROM backup_files 
                        WHERE job_id = ? 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    )
                """, (job_id, job_id, policy_value))
                
            elif policy_type == 'keep_days':
                # Delete backups older than N days
                cursor.execute("""
                    DELETE FROM backup_files 
                    WHERE job_id = ? AND created_at < datetime('now', '-{} days')
                """.format(policy_value), (job_id,))
                
            elif policy_type == 'keep_size':
                # Keep backups until total size exceeds N MB
                cursor.execute("""
                    WITH ranked_files AS (
                        SELECT id, file_size,
                               SUM(file_size) OVER (ORDER BY created_at DESC) as running_total
                        FROM backup_files 
                        WHERE job_id = ?
                    )
                    DELETE FROM backup_files 
                    WHERE job_id = ? AND id IN (
                        SELECT id FROM ranked_files 
                        WHERE running_total > ?
                    )
                """, (job_id, job_id, policy_value * 1024 * 1024))  # Convert MB to bytes
            
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
