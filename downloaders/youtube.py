"""
YouTube Downloader using yt-dlp
Supports multiple qualities, audio extraction, Shorts, and live streams
"""

import os
import asyncio
import yt_dlp
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from config import DOWNLOADS_DIR, MAX_FILE_SIZE_BYTES, YOUTUBE_COOKIES_FILE
from utils.helpers import (
    sanitize_filename, is_shorts_url, is_live_url,
    format_duration, format_file_size
)


class YouTubeDownloader:
    def __init__(self):
        self.downloads_dir = Path(DOWNLOADS_DIR)
        self.downloads_dir.mkdir(exist_ok=True)
        self.active_downloads = {}
    
    def _get_ydl_opts(self, quality: str, download_id: str, progress_hook: Callable = None) -> Dict[str, Any]:
        """Get yt-dlp options based on quality preference"""
        output_template = str(self.downloads_dir / f"%(id)s_{download_id}.%(ext)s")
        
        if quality == "audio":
            format_spec = "bestaudio/best"
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            final_ext = "mp3"
        else:
            # Robust format selection with fallback chains for all YouTube videos including Shorts
            # bestvideo* matches video-only OR video+audio combined formats (more reliable)
            # The / operator provides fallback: single-stream -> DASH streams -> absolute best
            quality_map = {
                "144": "best[height<=144]/bestvideo*[height<=144]+bestaudio/best",
                "240": "best[height<=240]/bestvideo*[height<=240]+bestaudio/best",
                "360": "best[height<=360]/bestvideo*[height<=360]+bestaudio/best",
                "480": "best[height<=480]/bestvideo*[height<=480]+bestaudio/best",
                "720": "best[height<=720]/bestvideo*[height<=720]+bestaudio/best",
                "1080": "best[height<=1080]/bestvideo*[height<=1080]+bestaudio/best",
                "1440": "best[height<=1440]/bestvideo*[height<=1440]+bestaudio/best",
                "2160": "best[height<=2160]/bestvideo*[height<=2160]+bestaudio/best",
                "best": "bestvideo*+bestaudio/best",
            }
            format_spec = quality_map.get(quality, "best[height<=720]/bestvideo*[height<=720]+bestaudio/best")
            postprocessors = [{
                'key': 'FFmpegVideoConvertor',
                'preferre dformat': 'mp4',
            }]
            final_ext = "mp4"
        
        opts = {
            'format': format_spec,
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'postprocessors': postprocessors,
            'noplaylist': True,
            'max_filesize': MAX_FILE_SIZE_BYTES,
            'retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            'keepvideo': False,
            'merge_output_format': 'mp4',
        }
        
        # Add cookies if available
        if YOUTUBE_COOKIES_FILE and os.path.exists(YOUTUBE_COOKIES_FILE):
            opts['cookiefile'] = YOUTUBE_COOKIES_FILE
        
        # Add progress hook
        if progress_hook:
            opts['progress_hooks'] = [progress_hook]
        
        return opts, final_ext
    
    async def get_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get video information without downloading"""
        try:
            loop = asyncio.get_event_loop()
            
            def _extract_info():
                opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                }
                if YOUTUBE_COOKIES_FILE and os.path.exists(YOUTUBE_COOKIES_FILE):
                    opts['cookiefile'] = YOUTUBE_COOKIES_FILE
                
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            info = await loop.run_in_executor(None, _extract_info)
            
            if info:
                return {
                    'id': info.get('id', ''),
                    'title': info.get('title', 'Unknown'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'description': info.get('description', ''),
                    'formats': info.get('formats', []),
                    'is_live': info.get('is_live', False),
                    'was_live': info.get('was_live', False),
                    'upload_date': info.get('upload_date', ''),
                    'is_shorts': is_shorts_url(url),
                    'webpage_url': info.get('webpage_url', url),
                }
            return None
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    async def download(self, url: str, quality: str, download_id: str,
                      progress_callback: Callable = None) -> Optional[Dict[str, Any]]:
        """
        Download a YouTube video
        Returns dict with file_path, title, duration, file_size
        """
        try:
            loop = asyncio.get_event_loop()
            result = {"file_path": None, "title": "", "duration": 0, "file_size": 0, "thumbnail": None}
            
            # Progress hook for yt-dlp
            def progress_hook(d):
                if d['status'] == 'downloading' and progress_callback:
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                    asyncio.run_coroutine_threadsafe(
                        progress_callback(downloaded, total, "downloading"), 
                        loop
                    )
                elif d['status'] == 'finished' and progress_callback:
                    asyncio.run_coroutine_threadsafe(
                        progress_callback(100, 100, "processing"), 
                        loop
                    )
            
            # Get options
            ydl_opts, final_ext = self._get_ydl_opts(quality, download_id, progress_hook)
            
            # Download
            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    
                    # Find the downloaded file
                    video_id = info.get('id', '')
                    expected_file = self.downloads_dir / f"{video_id}_{download_id}.{final_ext}"
                    
                    if not expected_file.exists():
                        # Try to find the file
                        for f in self.downloads_dir.glob(f"{video_id}_{download_id}.*"):
                            if f.is_file():
                                expected_file = f
                                break
                    
                    return {
                        'file_path': str(expected_file) if expected_file.exists() else None,
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'thumbnail': info.get('thumbnail', ''),
                        'uploader': info.get('uploader', ''),
                        'upload_date': info.get('upload_date', ''),
                        'view_count': info.get('view_count', 0),
                    }
            
            download_result = await asyncio.wait_for(
                loop.run_in_executor(None, _download),
                timeout=300  # 5 minute timeout
            )
            
            if download_result['file_path'] and os.path.exists(download_result['file_path']):
                file_size = os.path.getsize(download_result['file_path'])
                
                result.update({
                    'file_path': download_result['file_path'],
                    'title': download_result['title'],
                    'duration': download_result['duration'],
                    'file_size': file_size,
                    'thumbnail': download_result['thumbnail'],
                    'uploader': download_result['uploader'],
                    'upload_date': download_result['upload_date'],
                    'view_count': download_result['view_count'],
                })
            
            return result
            
        except asyncio.TimeoutError:
            result['error'] = "Download timed out. Try lower quality."
            return result
        except Exception as e:
            error_msg = str(e)
            if "filesize" in error_msg.lower():
                result['error'] = "File too large. Try lower quality or audio only."
            elif "private" in error_msg.lower() or "unavailable" in error_msg.lower():
                result['error'] = "This video is private or unavailable."
            elif "copyright" in error_msg.lower():
                result['error'] = "This video is blocked due to copyright."
            else:
                result['error'] = f"Download failed: {error_msg[:100]}"
            return result
    
    def cleanup(self, file_path: str):
        """Remove downloaded file"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
    
    async def get_available_qualities(self, url: str) -> list:
        """Get available qualities for a video"""
        try:
            info = await self.get_info(url)
            if not info or not info.get('formats'):
                return ["720", "360", "audio"]
            
            qualities = set()
            for fmt in info['formats']:
                height = fmt.get('height')
                if height:
                    if height >= 2160:
                        qualities.add("2160")
                    elif height >= 1440:
                        qualities.add("1440")
                    elif height >= 1080:
                        qualities.add("1080")
                    elif height >= 720:
                        qualities.add("720")
                    elif height >= 480:
                        qualities.add("480")
                    elif height >= 360:
                        qualities.add("360")
                    elif height >= 240:
                        qualities.add("240")
                    else:
                        qualities.add("144")
            
            result = []
            for q in ["2160", "1440", "1080", "720", "480", "360", "240", "144"]:
                if q in qualities:
                    result.append(q)
            
            if not result:
                result = ["720", "360"]
            
            result.append("audio")
            return result
            
        except Exception:
            return ["720", "360", "audio"]
