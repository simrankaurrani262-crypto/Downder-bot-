"""
Elite YouTube & Instagram Video Downloader Bot - Configuration
Master-level Telegram bot with advanced features
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)
DATABASE_PATH = BASE_DIR / "bot_database.db"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Telegram Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# Instagram Configuration
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")
INSTAGRAM_SESSION_FILE = BASE_DIR / "instagram_session.json"

# RapidAPI Configuration (for Instagram fallback)
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com")

# Bot Settings
BOT_NAME = os.getenv("BOT_NAME", "Video Downloader Pro")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))  # Telegram limit
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_DOWNLOAD_TIME = int(os.getenv("MAX_DOWNLOAD_TIME", "300"))  # 5 minutes timeout
CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", "3600"))  # Cleanup every hour

# Rate Limiting
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_DOWNLOADS_PER_MINUTE = int(os.getenv("RATE_LIMIT_DOWNLOADS_PER_MINUTE", "5"))
RATE_LIMIT_DOWNLOADS_PER_HOUR = int(os.getenv("RATE_LIMIT_DOWNLOADS_PER_HOUR", "30"))

# YouTube Settings
YOUTUBE_COOKIES_FILE = os.getenv("YOUTUBE_COOKIES_FILE", "")
YOUTUBE_DEFAULT_QUALITY = os.getenv("YOUTUBE_DEFAULT_QUALITY", "720")

# Feature Flags
ENABLE_YOUTUBE = os.getenv("ENABLE_YOUTUBE", "true").lower() == "true"
ENABLE_INSTAGRAM = os.getenv("ENABLE_INSTAGRAM", "true").lower() == "true"
ENABLE_AUDIO_MODE = os.getenv("ENABLE_AUDIO_MODE", "true").lower() == "true"
ENABLE_STATS = os.getenv("ENABLE_STATS", "true").lower() == "true"
ENABLE_BROADCAST = os.getenv("ENABLE_BROADCAST", "true").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Supported platforms regex patterns
YOUTUBE_PATTERNS = [
    r'(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/.+',
    r'(?:https?://)?(?:www\.)?youtube\.com/shorts/.+',
    r'(?:https?://)?(?:www\.)?youtube\.com/live/.+',
    r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=.+',
]

INSTAGRAM_PATTERNS = [
    r'(?:https?://)?(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/.+',
    r'(?:https?://)?(?:www\.)?instagram\.com/stories/.+',
    r'(?:https?://)?(?:www\.)?instagram\.com/share/.+',
    r'(?:https?://)?(?:www\.)?instagr\.am/.+',
]

# Quality presets for YouTube
QUALITY_PRESETS = {
    "audio": {"format": "bestaudio/best", "ext": "mp3", "label": "Audio Only (MP3)"},
    "144": {"format": "best[height<=144]/worst", "label": "144p"},
    "240": {"format": "best[height<=240]", "label": "240p"},
    "360": {"format": "best[height<=360]", "label": "360p"},
    "480": {"format": "best[height<=480]", "label": "480p"},
    "720": {"format": "best[height<=720]", "label": "720p HD"},
    "1080": {"format": "best[height<=1080]", "label": "1080p FHD"},
    "1440": {"format": "best[height<=1440]", "label": "1440p 2K"},
    "2160": {"format": "best[height<=2160]", "label": "2160p 4K"},
    "best": {"format": "best", "label": "Best Quality"},
}

# Messages
WELCOME_MESSAGE = """
Welcome to <b>{bot_name}</b> 

I'm your ultimate video downloader! I can download videos from:

YouTube:
- Regular videos
- Shorts
- Live streams
- Playlists (coming soon)

Instagram:
- Reels
- Video posts
- IGTV
- Stories (when available)

<b>How to use:</b>
Simply send me a YouTube or Instagram link, and I'll download it for you!

Use /help to see all available commands.
"""

HELP_MESSAGE = """
<b>Available Commands:</b>

/start - Start the bot
/help - Show this help message
/settings - Customize your preferences
/stats - View your download statistics

<b>Admin Commands:</b>
/stats all - View all users statistics
/users - List all users
/broadcast - Send message to all users
/maintenance - Toggle maintenance mode
/logs - View recent logs

<b>How to download:</b>
1. Send a YouTube or Instagram link
2. Choose your preferred quality
3. Wait for the download to complete

<b>Tips:</b>
- For audio only, select "Audio (MP3)" option
- Large files are automatically compressed
- Downloads are deleted from server after sending
"""

ADMIN_HELP = """
<b>Admin Panel - Available Commands:</b>

/stats all - Global bot statistics
/users - List all registered users
/broadcast &lt;message&gt; - Broadcast to all users
/broadcast_pin &lt;message&gt; - Broadcast and pin
/maintenance &lt;on/off&gt; - Toggle maintenance mode
/logs - View last 50 log lines
/ban &lt;user_id&gt; - Ban a user
/unban &lt;user_id&gt; - Unban a user
/user_info &lt;user_id&gt; - Get user details

<b>Inline Admin Buttons:</b>
Use admin panel from /admin command
"""

# Error messages
ERROR_MESSAGES = {
    "invalid_url": "Invalid URL. Please send a valid YouTube or Instagram link.",
    "download_failed": "Download failed. Please try again later or check if the content is available.",
    "file_too_large": "File is too large for Telegram. Try a lower quality option.",
    "rate_limited": "You're downloading too fast. Please wait a moment.",
    "maintenance": "Bot is under maintenance. Please try again later.",
    "not_admin": "You are not authorized to use this command.",
    "private_content": "This content is private. I cannot access it.",
    "unsupported": "This content type is not supported yet.",
    "timeout": "Download took too long. Please try again with lower quality.",
}

# Maintenance mode
maintenance_mode = False

# Validate configuration
def validate_config():
    """Validate essential configuration"""
    errors = []
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is required! Set it in .env file.")
    if not ADMIN_IDS:
        errors.append("ADMIN_IDS is recommended. Set at least one admin ID.")
    return errors
