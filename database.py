import sqlite3
import os
import logging
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """SQLite database manager for user projects and sessions"""
    
    def __init__(self, db_path="zendriver.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create user_projects table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT UNIQUE NOT NULL,
                        project_id TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create user_credentials table (optional - for account management)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_credentials (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT UNIQUE NOT NULL,
                        email TEXT NOT NULL,
                        account_status TEXT DEFAULT 'active',
                        credits_status TEXT DEFAULT 'available',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create job_history table (for tracking)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS job_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id TEXT UNIQUE NOT NULL,
                        user_id TEXT NOT NULL,
                        prompt TEXT NOT NULL,
                        status TEXT NOT NULL,
                        video_filename TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_user_project(self, user_id):
        """Get project ID for user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT project_id FROM user_projects WHERE user_id = ?", 
                    (user_id,)
                )
                result = cursor.fetchone()
                return result['project_id'] if result else None
        except Exception as e:
            logger.error(f"Error getting user project: {e}")
            return None
    
    def set_user_project(self, user_id, project_id):
        """Set project ID for user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_projects (user_id, project_id, updated_at) 
                    VALUES (?, ?, ?)
                ''', (user_id, project_id, datetime.now()))
                conn.commit()
                logger.info(f"User project saved: {user_id} -> {project_id}")
                return True
        except Exception as e:
            logger.error(f"Error setting user project: {e}")
            return False
    
    def get_all_user_projects(self):
        """Get all user projects as dictionary"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, project_id FROM user_projects")
                results = cursor.fetchall()
                return {row['user_id']: row['project_id'] for row in results}
        except Exception as e:
            logger.error(f"Error getting all user projects: {e}")
            return {}
    
    def save_user_credentials(self, user_id, email, account_status="active"):
        """Save user credentials info"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_credentials 
                    (user_id, email, account_status, updated_at) 
                    VALUES (?, ?, ?, ?)
                ''', (user_id, email, account_status, datetime.now()))
                conn.commit()
                logger.info(f"User credentials saved: {user_id} -> {email}")
                return True
        except Exception as e:
            logger.error(f"Error saving user credentials: {e}")
            return False
    
    def update_account_status(self, user_id, credits_status):
        """Update user account credits status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_credentials 
                    SET credits_status = ?, updated_at = ? 
                    WHERE user_id = ?
                ''', (credits_status, datetime.now(), user_id))
                conn.commit()
                logger.info(f"Account status updated: {user_id} -> {credits_status}")
                return True
        except Exception as e:
            logger.error(f"Error updating account status: {e}")
            return False
    
    def save_job_history(self, job_id, user_id, prompt, status, video_filename=None):
        """Save job to history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO job_history 
                    (job_id, user_id, prompt, status, video_filename, completed_at) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (job_id, user_id, prompt, status, video_filename, datetime.now()))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving job history: {e}")
            return False
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_jobs,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_jobs,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs
                    FROM job_history 
                    WHERE user_id = ?
                ''', (user_id,))
                result = cursor.fetchone()
                return dict(result) if result else {}
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
    
    def cleanup_old_records(self, days_old=30):
        """Clean up old job history records"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM job_history 
                    WHERE created_at < datetime('now', '-{} days')
                '''.format(days_old))
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"Cleaned up {deleted_count} old job records")
                return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
            return 0