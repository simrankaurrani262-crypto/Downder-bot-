"""
Helper utilities for the bot
URL detection, formatting, validation
"""

import re
import os
import time
import humanize
from typing import Optional, Dict, Any
from urllib.parse import urlparse


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube link"""
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/.+',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/.+',
        r'(?:https?://)?(?:www\.)?youtube\.com/live/.+',
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=.+',
        r'(?:https?://)?youtu\.be/.+',
    ]
    return any(re.match(pattern, url.strip()) for pattern in youtube_patterns)


def is_instagram_url(url: str) -> bool:
    """Check if URL is an Instagram link"""
    instagram_patterns = [
        r'(?:https?://)?(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/.+',
        r'(?:https?://)?(?:www\.)?instagram\.com/stories/.+',
        r'(?:https?://)?(?:www\.)?instagram\.com/share/.+',
        r'(?:https?://)?(?:www\.)?instagr\.am/.+',
    ]
    return any(re.match(pattern, url.strip()) for pattern in instagram_patterns)


def get_platform(url: str) -> Optional[str]:
    """Detect platform from URL"""
    if is_youtube_url(url):
        return "youtube"
    elif is_instagram_url(url):
        return "instagram"
    return None


def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/|youtube\.com/live/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_instagram_shortcode(url: str) -> Optional[str]:
    """Extract Instagram shortcode from URL"""
    patterns = [
        r'instagram\.com/(?:p|reel|reels|tv)/([a-zA-Z0-9_-]+)',
        r'instagram\.com/stories/[^/]+/(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def format_duration(seconds: int) -> str:
    """Format seconds to readable duration"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"


def format_file_size(bytes_size: int) -> str:
    """Format bytes to human readable size"""
    return humanize.naturalsize(bytes_size, binary=True)


def format_number(num: int) -> str:
    """Format large numbers"""
    return humanize.intcomma(num)


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """Sanitize filename for filesystem"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)
    # Limit length
    if len(filename) > max_length:
        filename = filename[:max_length].strip()
    return filename.strip()


def is_shorts_url(url: str) -> bool:
    """Check if YouTube URL is a Shorts video"""
    return 'shorts' in url.lower()


def is_live_url(url: str) -> bool:
    """Check if YouTube URL is a live stream"""
    return 'live' in url.lower() and 'youtube' in url.lower()


def cleanup_file(filepath: str):
    """Safely delete a file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass


def cleanup_old_files(directory: str, max_age_hours: int = 1):
    """Clean up files older than specified hours"""
    try:
        now = time.time()
        max_age = max_age_hours * 3600
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > max_age:
                    os.remove(filepath)
    except Exception:
        pass


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis"""
    if len(text) > max_length:
        return text[:max_length - 3].strip() + "..."
    return text


def create_progress_bar(percentage: float, length: int = 20) -> str:
    """Create a text progress bar"""
    filled = int(length * percentage / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percentage:.1f}%"


def escape_markdown(text: str) -> str:
    """Escape markdown characters for Telegram"""
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars:
        text = text.replace(char, f'\\{char}')
    return text


def format_video_info(info: Dict[str, Any]) -> str:
    """Format video information for display"""
    title = info.get('title', 'Unknown')
    duration = info.get('duration', 0)
    uploader = info.get('uploader', 'Unknown')
    view_count = info.get('view_count', 0)
    
    text = f"📹 <b>{truncate_text(title, 100)}</b>\n\n"
    text += f"👤 <b>Channel:</b> {uploader}\n"
    if duration:
        text += f"⏱ <b>Duration:</b> {format_duration(duration)}\n"
    if view_count:
        text += f"👁 <b>Views:</b> {format_number(view_count)}\n"
    
    return text


def get_quality_label(quality: str) -> str:
    """Get human readable quality label"""
    quality_map = {
        "audio": "🎵 Audio Only",
        "144": "144p",
        "240": "240p",
        "360": "360p",
        "480": "480p",
        "720": "720p HD",
        "1080": "1080p FHD",
        "1440": "1440p 2K",
        "2160": "2160p 4K",
        "best": "Best Quality",
    }
    return quality_map.get(quality, quality)
