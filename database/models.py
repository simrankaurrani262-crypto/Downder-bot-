"""
Data models for the bot database
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    joined_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    total_downloads: int = 0
    is_banned: bool = False
    default_quality: str = "720"
    preferred_format: str = "video"  # video or audio


@dataclass
class Download:
    id: Optional[int] = None
    user_id: int = 0
    url: str = ""
    platform: str = ""  # youtube, instagram
    title: str = ""
    quality: str = ""
    file_size: int = 0
    duration: int = 0
    download_time: float = 0.0
    status: str = "pending"  # pending, completed, failed
    error_message: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BotStats:
    total_users: int = 0
    total_downloads: int = 0
    active_today: int = 0
    active_week: int = 0
    youtube_downloads: int = 0
    instagram_downloads: int = 0
    failed_downloads: int = 0
    avg_download_time: float = 0.0
