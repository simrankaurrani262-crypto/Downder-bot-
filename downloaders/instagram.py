"""
Instagram Downloader
Supports Reels, Posts, IGTV, Stories
Uses multiple methods: yt-dlp, instaloader, RapidAPI fallback
"""

import os
import json
import asyncio
import logging
import aiohttp
import instaloader
import yt_dlp
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from config import (
    DOWNLOADS_DIR, MAX_FILE_SIZE_BYTES,
    INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, INSTAGRAM_SESSION_FILE,
    RAPIDAPI_KEY, RAPIDAPI_HOST
)
from utils.helpers import sanitize_filename

logger = logging.getLogger(__name__)


class InstagramDownloader:
    def __init__(self):
        self.downloads_dir = Path(DOWNLOADS_DIR)
        self.downloads_dir.mkdir(exist_ok=True)
        self.loader = None
        self.session = None
        self._init_instaloader()

    def _init_instaloader(self):
        """Initialize instaloader session"""
        try:
            self.loader = instaloader.Instaloader(
                download_pictures=False,
                download_videos=True,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                post_metadata_txt_pattern='',
                dirname_pattern=str(self.downloads_dir),
                filename_pattern='{shortcode}',
                quiet=True,
            )

            # Try to load session
            if INSTAGRAM_SESSION_FILE.exists():
                try:
                    self.loader.load_session_from_file(
                        INSTAGRAM_USERNAME if INSTAGRAM_USERNAME else "session",
                        str(INSTAGRAM_SESSION_FILE)
                    )
                except Exception:
                    pass
            elif INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
                try:
                    self.loader.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                    self.loader.save_session_to_file(str(INSTAGRAM_SESSION_FILE))
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Instaloader init error: {e}")
            self.loader = None

    async def get_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get Instagram post information"""
        try:
            # Try yt-dlp first
            info = await self._get_info_ytdlp(url)
            if info:
                return info

            # Try instaloader
            info = await self._get_info_instaloader(url)
            if info:
                return info

            # Try RapidAPI
            info = await self._get_info_rapidapi(url)
            if info:
                return info

            return None

        except Exception as e:
            logger.error(f"Error getting Instagram info: {e}")
            return None

    async def _get_info_ytdlp(self, url: str) -> Optional[Dict[str, Any]]:
        """Get info using yt-dlp"""
        try:
            loop = asyncio.get_event_loop()

            def _extract():
                opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'skip_download': True,
                    'ignore_no_formats_error': True,
                }
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(url, download=False)

            info = await loop.run_in_executor(None, _extract)

            if info:
                # Handle playlist/entries
                if 'entries' in info and info['entries']:
                    info = info['entries'][0]

                return {
                    'id': info.get('id', ''),
                    'title': info.get('title', 'Instagram Post'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'comment_count': info.get('comment_count', 0),
                    'upload_date': info.get('upload_date', ''),
                    'is_video': True,
                    'url': url,
                }
            return None

        except Exception as e:
            logger.debug(f"yt-dlp Instagram info failed: {e}")
            return None

    async def _get_info_instaloader(self, url: str) -> Optional[Dict[str, Any]]:
        """Get info using instaloader"""
        if not self.loader:
            return None

        try:
            from utils.helpers import extract_instagram_shortcode
            shortcode = extract_instagram_shortcode(url)
            if not shortcode:
                return None

            loop = asyncio.get_event_loop()

            def _get_post():
                post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
                return {
                    'id': shortcode,
                    'title': post.caption[:100] if post.caption else 'Instagram Post',
                    'uploader': post.owner_username,
                    'duration': 0,
                    'thumbnail': str(post.url) if post.url else '',
                    'description': post.caption if post.caption else '',
                    'view_count': post.video_view_count if post.is_video else post.likes,
                    'like_count': post.likes,
                    'comment_count': post.comments,
                    'upload_date': post.date_local.strftime('%Y%m%d') if post.date_local else '',
                    'is_video': post.is_video,
                    'url': url,
                }

            return await loop.run_in_executor(None, _get_post)

        except Exception as e:
            logger.debug(f"Instaloader info failed: {e}")
            return None

    async def _get_info_rapidapi(self, url: str) -> Optional[Dict[str, Any]]:
        """Get info using RapidAPI"""
        if not RAPIDAPI_KEY:
            return None

        try:
            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": RAPIDAPI_HOST,
            }

            params = {"url": url}

            async with self.session.get(
                f"https://{RAPIDAPI_HOST}/index",
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and isinstance(data, list) and len(data) > 0:
                        item = data[0]
                        return {
                            'id': item.get('id', ''),
                            'title': item.get('caption', 'Instagram Post')[:100],
                            'uploader': item.get('username', 'Unknown'),
                            'duration': 0,
                            'thumbnail': item.get('thumbnail_link', ''),
                            'description': item.get('caption', ''),
                            'url': url,
                        }
                return None

        except Exception as e:
            logger.debug(f"RapidAPI info failed: {e}")
            return None

    async def download(self, url: str, quality: str, download_id: str,
                      progress_callback: Callable = None) -> Optional[Dict[str, Any]]:
        """
        Download Instagram content
        Tries multiple methods in order
        """
        result = {
            'file_path': None, 'title': '', 'duration': 0,
            'file_size': 0, 'thumbnail': None, 'error': None
        }

        # Method 1: yt-dlp
        try:
            download_result = await self._download_ytdlp(url, quality, download_id, progress_callback)
            if download_result and download_result.get('file_path'):
                return download_result
        except Exception as e:
            logger.debug(f"yt-dlp download failed: {e}")
            result['error'] = str(e)

        # Method 2: instaloader
        try:
            download_result = await self._download_instaloader(url, quality, download_id, progress_callback)
            if download_result and download_result.get('file_path'):
                return download_result
        except Exception as e:
            logger.debug(f"Instaloader download failed: {e}")
            result['error'] = str(e)

        # Method 3: RapidAPI
        try:
            download_result = await self._download_rapidapi(url, quality, download_id, progress_callback)
            if download_result and download_result.get('file_path'):
                return download_result
        except Exception as e:
            logger.debug(f"RapidAPI download failed: {e}")
            result['error'] = str(e)

        if not result['error']:
            result['error'] = "Failed to download from Instagram. Content may be private or unavailable."

        return result

    async def _download_ytdlp(self, url: str, quality: str, download_id: str,
                             progress_callback: Callable = None) -> Optional[Dict[str, Any]]:
        """Download using yt-dlp"""
        try:
            loop = asyncio.get_event_loop()
            output_template = str(self.downloads_dir / f"ig_%(id)s_{download_id}.%(ext)s")

            def progress_hook(d):
                if d['status'] == 'downloading' and progress_callback:
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                    asyncio.run_coroutine_threadsafe(
                        progress_callback(downloaded, total, "downloading"),
                        loop
                    )

            if quality == "audio":
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': output_template,
                    'quiet': True,
                    'no_warnings': True,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'progress_hooks': [progress_hook] if progress_callback else [],
                    'max_filesize': MAX_FILE_SIZE_BYTES,
                    'ignore_no_formats_error': True,
                }
            else:
                ydl_opts = {
                    'format': 'best[ext=mp4]/best',
                    'outtmpl': output_template,
                    'quiet': True,
                    'no_warnings': True,
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferredformat': 'mp4',
                    }],
                    'progress_hooks': [progress_hook] if progress_callback else [],
                    'max_filesize': MAX_FILE_SIZE_BYTES,
                    'merge_output_format': 'mp4',
                    'ignore_no_formats_error': True,
                }

            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                    # Handle playlists
                    if 'entries' in info and info['entries']:
                        info = info['entries'][0]

                    video_id = info.get('id', '')
                    ext = 'mp3' if quality == 'audio' else 'mp4'
                    expected_file = self.downloads_dir / f"ig_{video_id}_{download_id}.{ext}"

                    if not expected_file.exists():
                        for f in self.downloads_dir.glob(f"ig_{video_id}_{download_id}.*"):
                            if f.is_file():
                                expected_file = f
                                break
                        if not expected_file.exists():
                            for f in self.downloads_dir.glob(f"ig_*_{download_id}.*"):
                                if f.is_file():
                                    expected_file = f
                                    break

                    return {
                        'file_path': str(expected_file) if expected_file.exists() else None,
                        'title': info.get('title', 'Instagram Post'),
                        'duration': info.get('duration', 0),
                        'thumbnail': info.get('thumbnail', ''),
                        'uploader': info.get('uploader', ''),
                    }

            download_result = await asyncio.wait_for(
                loop.run_in_executor(None, _download),
                timeout=300
            )

            if download_result['file_path'] and os.path.exists(download_result['file_path']):
                file_size = os.path.getsize(download_result['file_path'])
                return {
                    'file_path': download_result['file_path'],
                    'title': download_result['title'],
                    'duration': download_result['duration'],
                    'file_size': file_size,
                    'thumbnail': download_result['thumbnail'],
                    'uploader': download_result['uploader'],
                }
            return None

        except Exception as e:
            logger.debug(f"yt-dlp download error: {e}")
            return None

    async def _download_instaloader(self, url: str, quality: str, download_id: str,
                                   progress_callback: Callable = None) -> Optional[Dict[str, Any]]:
        """Download using instaloader"""
        if not self.loader:
            return None

        try:
            from utils.helpers import extract_instagram_shortcode
            shortcode = extract_instagram_shortcode(url)
            if not shortcode:
                return None

            loop = asyncio.get_event_loop()
            download_path = self.downloads_dir / f"ig_{shortcode}_{download_id}.mp4"

            def _download():
                post = instaloader.Post.from_shortcode(self.loader.context, shortcode)

                if not post.is_video and quality != "audio":
                    return None

                # Download video
                if post.is_video:
                    video_url = post.video_url
                    if video_url:
                        import urllib.request
                        urllib.request.urlretrieve(video_url, str(download_path))

                return {
                    'file_path': str(download_path) if download_path.exists() else None,
                    'title': post.caption[:100] if post.caption else 'Instagram Post',
                    'duration': 0,
                    'thumbnail': str(post.url) if post.url else '',
                    'uploader': post.owner_username,
                }

            if progress_callback:
                await progress_callback(0, 100, "downloading")

            download_result = await asyncio.wait_for(
                loop.run_in_executor(None, _download),
                timeout=300
            )

            if download_result and download_result.get('file_path'):
                file_size = os.path.getsize(download_result['file_path'])
                return {
                    **download_result,
                    'file_size': file_size,
                }
            return None

        except Exception as e:
            logger.debug(f"Instaloader download error: {e}")
            return None

    async def _download_rapidapi(self, url: str, quality: str, download_id: str,
                                progress_callback: Callable = None) -> Optional[Dict[str, Any]]:
        """Download using RapidAPI"""
        if not RAPIDAPI_KEY:
            return None

        try:
            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            if progress_callback:
                await progress_callback(0, 100, "downloading")

            # First get download URL from API
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": RAPIDAPI_HOST,
            }

            params = {"url": url}

            async with self.session.get(
                f"https://{RAPIDAPI_HOST}/index",
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                if not data or not isinstance(data, list) or len(data) == 0:
                    return None

                item = data[0]
                media_url = item.get('media_link', '') or item.get('video_url', '')

                if not media_url:
                    return None

                if progress_callback:
                    await progress_callback(50, 100, "downloading")

                # Download the file
                ext = 'mp3' if quality == 'audio' else 'mp4'
                download_path = self.downloads_dir / f"ig_api_{download_id}.{ext}"

                async with self.session.get(media_url, timeout=aiohttp.ClientTimeout(total=120)) as media_response:
                    if media_response.status == 200:
                        with open(download_path, 'wb') as f:
                            async for chunk in media_response.content.iter_chunked(8192):
                                f.write(chunk)

                if progress_callback:
                    await progress_callback(100, 100, "processing")

                if download_path.exists():
                    file_size = os.path.getsize(str(download_path))
                    return {
                        'file_path': str(download_path),
                        'title': item.get('caption', 'Instagram Post')[:100],
                        'duration': 0,
                        'file_size': file_size,
                        'thumbnail': item.get('thumbnail_link', ''),
                        'uploader': item.get('username', 'Unknown'),
                    }
                return None

        except Exception as e:
            logger.debug(f"RapidAPI download error: {e}")
            return None

    def cleanup(self, file_path: str):
        """Remove downloaded file"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
