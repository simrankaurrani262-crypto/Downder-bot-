"""
Database handler for the bot - SQLite
Handles users, downloads, and statistics
"""

import sqlite3
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from .models import User, Download, BotStats


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.local = threading.local()
        self.init_db()

    def get_connection(self):
        if not hasattr(self.local, 'connection') or self.local.connection is None:
            self.local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.local.connection.row_factory = sqlite3.Row
        return self.local.connection

    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT,
                joined_date TEXT,
                last_activity TEXT,
                total_downloads INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                default_quality TEXT DEFAULT '720',
                preferred_format TEXT DEFAULT 'video'
            )
        ''')

        # Downloads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                url TEXT,
                platform TEXT,
                title TEXT,
                quality TEXT,
                file_size INTEGER DEFAULT 0,
                duration INTEGER DEFAULT 0,
                download_time REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Rate limiting table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                user_id INTEGER PRIMARY KEY,
                minute_count INTEGER DEFAULT 0,
                hour_count INTEGER DEFAULT 0,
                last_reset TEXT,
                hour_reset TEXT
            )
        ''')

        conn.commit()

    # User methods
    def add_user(self, user: User) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, language_code, joined_date, last_activity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user.user_id, user.username, user.first_name, user.last_name,
                  user.language_code, user.joined_date, user.last_activity))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error adding user: {e}")
            return False

    def get_user(self, user_id: int) -> Optional[User]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            return User(
                user_id=row['user_id'],
                username=row['username'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                language_code=row['language_code'],
                joined_date=row['joined_date'],
                last_activity=row['last_activity'],
                total_downloads=row['total_downloads'],
                is_banned=bool(row['is_banned']),
                default_quality=row['default_quality'],
                preferred_format=row['preferred_format']
            )
        return None

    def update_user_activity(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET last_activity = ? WHERE user_id = ?',
            (datetime.now().isoformat(), user_id)
        )
        conn.commit()

    def update_user_settings(self, user_id: int, quality: str = None, format_pref: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if quality:
            cursor.execute('UPDATE users SET default_quality = ? WHERE user_id = ?', (quality, user_id))
        if format_pref:
            cursor.execute('UPDATE users SET preferred_format = ? WHERE user_id = ?', (format_pref, user_id))
        conn.commit()

    def increment_downloads(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET total_downloads = total_downloads + 1 WHERE user_id = ?',
            (user_id,)
        )
        conn.commit()

    def ban_user(self, user_id: int) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
            conn.commit()
            return True
        except Exception:
            return False

    def unban_user(self, user_id: int) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
            conn.commit()
            return True
        except Exception:
            return False

    def get_all_users(self) -> List[User]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY joined_date DESC')
        rows = cursor.fetchall()
        return [User(
            user_id=row['user_id'],
            username=row['username'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            is_banned=bool(row['is_banned']),
            total_downloads=row['total_downloads'],
            joined_date=row['joined_date'],
            last_activity=row['last_activity']
        ) for row in rows]

    def get_users_count(self) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        return cursor.fetchone()[0]

    # Download methods
    def add_download(self, download: Download) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO downloads (user_id, url, platform, title, quality, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (download.user_id, download.url, download.platform, download.title,
              download.quality, download.status, download.created_at))
        conn.commit()
        return cursor.lastrowid

    def update_download_status(self, download_id: int, status: str, 
                               file_size: int = None, duration: int = None,
                               download_time: float = None, error: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        updates = ["status = ?"]
        values = [status]
        if file_size is not None:
            updates.append("file_size = ?")
            values.append(file_size)
        if duration is not None:
            updates.append("duration = ?")
            values.append(duration)
        if download_time is not None:
            updates.append("download_time = ?")
            values.append(download_time)
        if error is not None:
            updates.append("error_message = ?")
            values.append(error)
        values.append(download_id)
        cursor.execute(f'UPDATE downloads SET {", ".join(updates)} WHERE id = ?', values)
        conn.commit()

    def get_user_downloads(self, user_id: int, limit: int = 10) -> List[Download]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM downloads WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit)
        )
        rows = cursor.fetchall()
        return [Download(
            id=row['id'],
            user_id=row['user_id'],
            url=row['url'],
            platform=row['platform'],
            title=row['title'],
            quality=row['quality'],
            file_size=row['file_size'],
            duration=row['duration'],
            status=row['status'],
            created_at=row['created_at']
        ) for row in rows]

    def get_download_stats(self) -> Dict[str, int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        stats = {}
        cursor.execute('SELECT COUNT(*) FROM downloads WHERE status = "completed"')
        stats['total_completed'] = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM downloads WHERE status = "failed"')
        stats['total_failed'] = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM downloads WHERE platform = "youtube"')
        stats['youtube_count'] = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM downloads WHERE platform = "instagram"')
        stats['instagram_count'] = cursor.fetchone()[0]
        return stats

    # Rate limiting
    def check_rate_limit(self, user_id: int) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now()
        
        cursor.execute('SELECT * FROM rate_limits WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if not row:
            cursor.execute('''
                INSERT INTO rate_limits (user_id, minute_count, hour_count, last_reset, hour_reset)
                VALUES (?, 1, 1, ?, ?)
            ''', (user_id, now.isoformat(), now.isoformat()))
            conn.commit()
            return {"allowed": True, "minute_remaining": 4, "hour_remaining": 29}
        
        last_reset = datetime.fromisoformat(row['last_reset'])
        hour_reset = datetime.fromisoformat(row['hour_reset'])
        
        # Reset minute counter
        if now - last_reset > timedelta(minutes=1):
            minute_count = 1
            last_reset = now
        else:
            minute_count = row['minute_count'] + 1
        
        # Reset hour counter
        if now - hour_reset > timedelta(hours=1):
            hour_count = 1
            hour_reset = now
        else:
            hour_count = row['hour_count'] + 1
        
        cursor.execute('''
            UPDATE rate_limits 
            SET minute_count = ?, hour_count = ?, last_reset = ?, hour_reset = ?
            WHERE user_id = ?
        ''', (minute_count, hour_count, last_reset.isoformat(), hour_reset.isoformat(), user_id))
        conn.commit()
        
        from config import RATE_LIMIT_DOWNLOADS_PER_MINUTE, RATE_LIMIT_DOWNLOADS_PER_HOUR
        
        allowed = (minute_count <= RATE_LIMIT_DOWNLOADS_PER_MINUTE and 
                  hour_count <= RATE_LIMIT_DOWNLOADS_PER_HOUR)
        
        return {
            "allowed": allowed,
            "minute_remaining": max(0, RATE_LIMIT_DOWNLOADS_PER_MINUTE - minute_count),
            "hour_remaining": max(0, RATE_LIMIT_DOWNLOADS_PER_HOUR - hour_count),
            "minute_count": minute_count,
            "hour_count": hour_count
        }

    # Statistics
    def get_bot_stats(self) -> BotStats:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM downloads WHERE status = "completed"')
        total_downloads = cursor.fetchone()[0]
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM downloads WHERE created_at LIKE ?', (f'{today}%',))
        active_today = cursor.fetchone()[0]
        
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM downloads WHERE created_at > ?', (week_ago,))
        active_week = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM downloads WHERE platform = "youtube" AND status = "completed"')
        youtube_downloads = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM downloads WHERE platform = "instagram" AND status = "completed"')
        instagram_downloads = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM downloads WHERE status = "failed"')
        failed_downloads = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(download_time) FROM downloads WHERE status = "completed"')
        avg_time = cursor.fetchone()[0] or 0
        
        return BotStats(
            total_users=total_users,
            total_downloads=total_downloads,
            active_today=active_today,
            active_week=active_week,
            youtube_downloads=youtube_downloads,
            instagram_downloads=instagram_downloads,
            failed_downloads=failed_downloads,
            avg_download_time=round(avg_time, 2)
        )
