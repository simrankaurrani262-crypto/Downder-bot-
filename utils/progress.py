"""
Progress tracking for downloads and uploads
"""

import time
import asyncio
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.helpers import create_progress_bar, format_file_size


class DownloadProgress:
    """Track download progress and update messages"""
    
    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE, title: str = "Downloading..."):
        self.update = update
        self.context = context
        self.title = title
        self.message = None
        self.start_time = time.time()
        self.last_update = 0
        self.update_interval = 3  # Update every 3 seconds
        self.cancelled = False
    
    async def start(self):
        """Send initial progress message"""
        try:
            text = f"⬇️ <b>Starting Download...</b>\n\n📹 <i>{self.title[:50]}...</i>\n\n{create_progress_bar(0)}"
            # In callback query context update.message is None; use the query message's chat
            if self.update.callback_query:
                chat_id = self.update.callback_query.message.chat_id
                self.message = await self.update.callback_query.get_bot().send_message(
                    chat_id=chat_id, text=text, parse_mode="HTML"
                )
            elif self.update.message:
                self.message = await self.update.message.reply_text(text, parse_mode="HTML")
        except Exception:
            pass
    
    async def update_progress(self, downloaded: int, total: int, status: str = "downloading"):
        """Update progress message"""
        if self.cancelled:
            return
        
        current_time = time.time()
        if current_time - self.last_update < self.update_interval and downloaded < total:
            return
        
        self.last_update = current_time
        
        try:
            if total > 0:
                percentage = (downloaded / total) * 100
                elapsed = current_time - self.start_time
                speed = downloaded / elapsed if elapsed > 0 else 0
                
                if speed > 0 and downloaded < total:
                    remaining = (total - downloaded) / speed
                    eta_text = f"{int(remaining)}s"
                else:
                    eta_text = "calculating..."
                
                if status == "downloading":
                    text = f"⬇️ <b>Downloading...</b>\n\n"
                elif status == "processing":
                    text = f"🔄 <b>Processing...</b>\n\n"
                elif status == "uploading":
                    text = f"⬆️ <b>Uploading to Telegram...</b>\n\n"
                else:
                    text = f"⏳ <b>{status.capitalize()}...</b>\n\n"
                
                text += f"📹 <i>{self.title[:60]}</i>\n"
                text += f"{create_progress_bar(percentage)}\n\n"
                text += f"📊 <b>Size:</b> {format_file_size(downloaded)} / {format_file_size(total)}\n"
                text += f"⚡ <b>Speed:</b> {format_file_size(int(speed))}/s\n"
                text += f"⏱ <b>ETA:</b> {eta_text}"
                
                if self.message:
                    await self.message.edit_text(text, parse_mode="HTML")
        except Exception:
            pass  # Ignore edit errors (message not changed or deleted)
    
    async def complete(self):
        """Mark download as complete"""
        if self.cancelled:
            return
        try:
            if self.message:
                await self.message.delete()
        except Exception:
            pass
    
    async def error(self, error_msg: str):
        """Show error in progress"""
        try:
            if self.message:
                text = f"❌ <b>Download Failed</b>\n\n{error_msg}"
                await self.message.edit_text(text, parse_mode="HTML")
        except Exception:
            pass
    
    def cancel(self):
        """Cancel the download"""
        self.cancelled = True


class UploadProgress:
    """Track upload progress to Telegram"""
    
    def __init__(self, message, total_size: int):
        self.message = message
        self.total_size = total_size
        self.uploaded = 0
        self.last_update = 0
        self.update_interval = 4
        self.start_time = time.time()
    
    async def __call__(self, uploaded_bytes: int, total_bytes: int):
        """Called during upload"""
        self.uploaded = uploaded_bytes
        current_time = time.time()
        
        if current_time - self.last_update < self.update_interval:
            return
        
        self.last_update = current_time
        
        try:
            if total_bytes > 0:
                percentage = (uploaded_bytes / total_bytes) * 100
                text = f"⬆️ <b>Uploading to Telegram...</b>\n\n{create_progress_bar(percentage)}\n\n"
                text += f"📊 {format_file_size(uploaded_bytes)} / {format_file_size(total_bytes)}"
                await self.message.edit_text(text, parse_mode="HTML")
        except Exception:
            pass
