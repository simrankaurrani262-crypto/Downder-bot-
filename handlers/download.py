"""
Download handlers - Main URL processing and quality selection
"""

import os
import uuid
import asyncio
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from config import (
    ENABLE_YOUTUBE, ENABLE_INSTAGRAM, ENABLE_AUDIO_MODE,
    MAX_FILE_SIZE_BYTES, BOT_NAME
)
from database import Database
from database.models import Download
from downloaders import YouTubeDownloader, InstagramDownloader
from utils.helpers import (
    is_youtube_url, is_instagram_url, get_platform,
    format_video_info, format_file_size, format_duration,
    cleanup_file
)
from utils.keyboard import quality_selection_keyboard, cancel_keyboard
from utils.progress import DownloadProgress

logger = logging.getLogger(__name__)

# Store active downloads
active_downloads = {}


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages - detect URLs"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user = update.effective_user

    # Update user activity
    db: Database = context.bot_data.get('db')
    if db:
        db.update_user_activity(user.id)

    # Check if it's a URL
    if is_youtube_url(text):
        if not ENABLE_YOUTUBE:
            await update.message.reply_text("❌ YouTube downloads are currently disabled.")
            return
        await handle_youtube_url(update, context, text)

    elif is_instagram_url(text):
        if not ENABLE_INSTAGRAM:
            await update.message.reply_text("❌ Instagram downloads are currently disabled.")
            return
        await handle_instagram_url(update, context, text)

    else:
        await update.message.reply_text(
            "❓ <b>Send me a YouTube or Instagram link to download!</b>\n\n"
            "Supported platforms:\n"
            "• YouTube videos, Shorts, Live streams\n"
            "• Instagram Reels, Posts, IGTV\n\n"
            "Use /help for more info.",
            parse_mode="HTML"
        )


async def handle_youtube_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """Handle YouTube URL - show quality selection"""
    processing_msg = None
    try:
        processing_msg = await update.message.reply_text("🔍 <b>Analyzing YouTube video...</b>", parse_mode="HTML")

        yt_downloader: YouTubeDownloader = context.bot_data.get('yt_downloader')

        # Try to get info with timeout
        try:
            info = await asyncio.wait_for(
                yt_downloader.get_info(url),
                timeout=30
            )
        except asyncio.TimeoutError:
            await processing_msg.edit_text(
                "⏱ <b>Analysis timed out.</b>\n"
                "The video might be too long or the server is busy. Please try again.",
                parse_mode="HTML"
            )
            return

        if not info:
            await processing_msg.edit_text(
                "❌ <b>Could not fetch video information.</b>\n\n"
                "Possible reasons:\n"
                "• Video is private or restricted\n"
                "• Video is age-restricted\n"
                "• Video was removed or is unavailable\n"
                "• URL is invalid\n\n"
                "Please check the link and try again.",
                parse_mode="HTML"
            )
            return

        await processing_msg.delete()

        if 'downloads' not in context.user_data:
            context.user_data['downloads'] = {}

        download_id = str(uuid.uuid4())[:8]
        context.user_data['downloads'][download_id] = {
            'url': url,
            'platform': 'youtube',
            'title': info.get('title', 'Unknown'),
        }

        info_text = format_video_info(info)
        info_text += f"\n<b>Select quality to download:</b>"

        keyboard = quality_selection_keyboard("youtube", is_youtube=True)

        await update.message.reply_text(
            info_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error handling YouTube URL {url}: {e}", exc_info=True)
        if processing_msg:
            try:
                await processing_msg.edit_text(
                    f"❌ <b>Error:</b> Could not process this link.\n"
                    f"Please try again or check if the URL is valid.",
                    parse_mode="HTML"
                )
            except Exception:
                await update.message.reply_text(
                    f"❌ <b>Error:</b> Could not process this link.",
                    parse_mode="HTML"
                )
        else:
            await update.message.reply_text(
                f"❌ <b>Error:</b> Could not process this link.",
                parse_mode="HTML"
            )


async def handle_instagram_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """Handle Instagram URL - show download options"""
    processing_msg = None
    try:
        processing_msg = await update.message.reply_text("🔍 <b>Analyzing Instagram post...</b>", parse_mode="HTML")

        ig_downloader: InstagramDownloader = context.bot_data.get('ig_downloader')

        # Try to get info with timeout
        try:
            info = await asyncio.wait_for(
                ig_downloader.get_info(url),
                timeout=30
            )
        except asyncio.TimeoutError:
            await processing_msg.edit_text(
                "⏱ <b>Analysis timed out.</b>\n"
                "Please try again later.",
                parse_mode="HTML"
            )
            return

        if not info:
            await processing_msg.edit_text(
                "❌ <b>Could not fetch post information.</b>\n"
                "The post might be private or unavailable.\n\n"
                "For private accounts, the owner needs to make it public first.",
                parse_mode="HTML"
            )
            return

        await processing_msg.delete()

        if 'downloads' not in context.user_data:
            context.user_data['downloads'] = {}

        download_id = str(uuid.uuid4())[:8]
        context.user_data['downloads'][download_id] = {
            'url': url,
            'platform': 'instagram',
            'title': info.get('title', 'Instagram Post'),
        }

        info_text = f"📸 <b>{info.get('title', 'Instagram Post')[:100]}</b>\n\n"
        if info.get('uploader'):
            info_text += f"👤 <b>User:</b> {info['uploader']}\n"
        if info.get('like_count'):
            info_text += f"❤️ <b>Likes:</b> {info['like_count']:,}\n"
        if info.get('comment_count'):
            info_text += f"💬 <b>Comments:</b> {info['comment_count']:,}\n"

        info_text += f"\n<b>Select download option:</b>"

        keyboard = quality_selection_keyboard("instagram", is_youtube=False)

        await update.message.reply_text(
            info_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error handling Instagram URL {url}: {e}", exc_info=True)
        if processing_msg:
            try:
                await processing_msg.edit_text(
                    "❌ <b>Error:</b> Could not process this Instagram link.",
                    parse_mode="HTML"
                )
            except Exception:
                await update.message.reply_text(
                    "❌ <b>Error:</b> Could not process this Instagram link.",
                    parse_mode="HTML"
                )
        else:
            await update.message.reply_text(
                "❌ <b>Error:</b> Could not process this Instagram link.",
                parse_mode="HTML"
            )


async def url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process download after quality selection"""
    query = update.callback_query
    user = update.effective_user
    callback_data = query.data

    if not callback_data.startswith("dl:"):
        return

    action = callback_data.split(":")[1]

    if action == "cancel":
        await query.edit_message_text("❌ <b>Download cancelled.</b>", parse_mode="HTML")
        return

    # Get stored download info
    downloads = context.user_data.get('downloads', {})

    download_info = None
    download_id = None

    for did, info in list(downloads.items()):
        download_info = info
        download_id = did
        break

    if not download_info:
        await query.edit_message_text(
            "❌ <b>Download expired. Please send the link again.</b>",
            parse_mode="HTML"
        )
        return

    url = download_info['url']
    platform = download_info['platform']
    quality = action

    # Track in database
    db: Database = context.bot_data.get('db')
    download_record_id = None
    if db:
        try:
            dl_record = Download(
                user_id=user.id,
                url=url,
                platform=platform,
                title=download_info.get('title', 'Unknown'),
                quality=quality,
                status='pending'
            )
            download_record_id = db.add_download(dl_record)
        except Exception as e:
            logger.warning(f"Could not create download record: {e}")

    await query.edit_message_text(
        f"⬇️ <b>Starting download...</b>\n\n"
        f"📹 <i>{download_info.get('title', 'Video')[:60]}</i>\n"
        f"🎯 <b>Quality:</b> {quality}",
        parse_mode="HTML"
    )

    # Create progress tracker - pass the callback query message for updates
    progress = DownloadProgress(update, context, download_info.get('title', 'Video'))

    try:
        if platform == 'youtube':
            result = await download_youtube(
                update, context, url, quality, download_id, progress
            )
        else:
            result = await download_instagram(
                update, context, url, quality, download_id, progress
            )

        if result and result.get('file_path') and os.path.exists(result['file_path']):
            await send_downloaded_file(update, context, result, platform, quality)

            if db:
                db.increment_downloads(user.id)
                if download_record_id:
                    db.update_download_status(
                        download_record_id, "completed",
                        file_size=result.get('file_size', 0),
                        duration=result.get('duration', 0)
                    )
        else:
            error = result.get('error', 'Download failed — file not found') if result else 'Download failed'
            await query.edit_message_text(
                f"❌ <b>Download Failed</b>\n\n"
                f"{error}\n\n"
                f"Try a different quality or check if the content is still available.",
                parse_mode="HTML"
            )
            if db and download_record_id:
                db.update_download_status(download_record_id, "failed", error=error)

    except Exception as e:
        logger.error(f"Download error: {e}", exc_info=True)
        error_msg = str(e)[:150]
        try:
            await query.edit_message_text(
                f"❌ <b>Download failed:</b>\n{error_msg}\n\n"
                f"Please try again with different settings.",
                parse_mode="HTML"
            )
        except Exception:
            pass
        if db and download_record_id:
            db.update_download_status(download_record_id, "failed", error=error_msg)
    finally:
        await progress.complete()
        if download_id and download_id in downloads:
            del downloads[download_id]


async def download_youtube(update, context, url, quality, download_id, progress):
    """Download YouTube video"""
    yt_downloader: YouTubeDownloader = context.bot_data.get('yt_downloader')

    await progress.start()

    result = await yt_downloader.download(
        url=url,
        quality=quality,
        download_id=download_id,
        progress_callback=progress.update_progress
    )

    return result


async def download_instagram(update, context, url, quality, download_id, progress):
    """Download Instagram content"""
    ig_downloader: InstagramDownloader = context.bot_data.get('ig_downloader')

    await progress.start()

    result = await ig_downloader.download(
        url=url,
        quality=quality,
        download_id=download_id,
        progress_callback=progress.update_progress
    )

    return result


async def send_downloaded_file(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               result: dict, platform: str, quality: str):
    """Send the downloaded file to user"""
    query = update.callback_query
    user = update.effective_user

    file_path = result.get('file_path')
    title = result.get('title', 'Video')
    duration = result.get('duration', 0)
    file_size = result.get('file_size', 0)
    uploader = result.get('uploader', '')

    if not file_path or not os.path.exists(file_path):
        await query.edit_message_text(
            "❌ <b>File not found after download.</b>",
            parse_mode="HTML"
        )
        return

    # Check file size
    actual_size = os.path.getsize(file_path)
    if actual_size > MAX_FILE_SIZE_BYTES:
        await query.edit_message_text(
            f"❌ <b>File too large!</b>\n\n"
            f"Size: {format_file_size(actual_size)}\n"
            f"Telegram limit: {format_file_size(MAX_FILE_SIZE_BYTES)}\n\n"
            f"Try lower quality or audio only.",
            parse_mode="HTML"
        )
        cleanup_file(file_path)
        return

    await query.edit_message_text(
        f"✅ <b>Download complete!</b>\n"
        f"📤 Sending file...",
        parse_mode="HTML"
    )

    # Build caption
    caption = f"📹 <b>{title[:200]}</b>\n"
    if uploader and uploader != 'Unknown':
        caption += f"👤 {uploader}\n"
    if duration:
        caption += f"⏱ {format_duration(duration)}\n"
    caption += f"📊 {format_file_size(actual_size)}\n"
    try:
        bot_username = context.bot.username
        if bot_username:
            caption += f"🤖 @{bot_username}"
    except Exception:
        pass

    try:
        is_audio = quality == "audio" or str(file_path).endswith('.mp3')

        if is_audio:
            with open(file_path, 'rb') as audio_file:
                await context.bot.send_audio(
                    chat_id=user.id,
                    audio=audio_file,
                    title=title[:100],
                    performer=uploader[:100] if uploader else None,
                    duration=int(duration) if duration else None,
                    caption=caption,
                    parse_mode="HTML"
                )
        else:
            with open(file_path, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=user.id,
                    video=video_file,
                    caption=caption,
                    parse_mode="HTML",
                    duration=int(duration) if duration else None,
                    supports_streaming=True
                )

        try:
            await query.delete_message()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Error sending file: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ <b>Failed to send file:</b>\n{str(e)[:150]}\n\n"
            f"The file might be too large or corrupted. Try a lower quality.",
            parse_mode="HTML"
        )
    finally:
        cleanup_file(file_path)
