#!/usr/bin/env python3
"""
Elite YouTube & Instagram Video Downloader Bot
Master-level Telegram Bot with advanced features

Features:
- YouTube video/shorts/live download (multiple qualities up to 4K)
- Instagram reel/post/IGTV download
- Audio-only extraction (MP3)
- User database & statistics
- Admin panel with broadcast
- Rate limiting
- Progress tracking
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# Configuration
from config import (
    BOT_TOKEN, ADMIN_IDS, DATABASE_PATH, LOGS_DIR,
    LOG_LEVEL, validate_config, maintenance_mode
)

# Database
from database import Database

# Downloaders
from downloaders import YouTubeDownloader, InstagramDownloader

# Handlers
from handlers.start import start_handler, help_handler
from handlers.download import message_handler
from handlers.admin import (
    admin_handler, stats_handler, users_handler, broadcast_handler,
    ban_handler, unban_handler, user_info_handler, logs_handler,
    maintenance_handler
)
from handlers.settings import settings_handler
from handlers.callbacks import callback_handler

# Utils
from utils.helpers import cleanup_old_files


# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class VideoDownloaderBot:
    """Main bot class"""
    
    def __init__(self):
        self.db = None
        self.yt_downloader = None
        self.ig_downloader = None
        self.application = None
    
    async def init_components(self):
        """Initialize bot components"""
        logger.info("Initializing bot components...")
        
        # Validate config
        errors = validate_config()
        if errors:
            for error in errors:
                logger.error(error)
            sys.exit(1)
        
        # Initialize database
        self.db = Database(str(DATABASE_PATH))
        logger.info("Database initialized")
        
        # Initialize downloaders
        self.yt_downloader = YouTubeDownloader()
        self.ig_downloader = InstagramDownloader()
        logger.info("Downloaders initialized")
    
    async def post_init(self, application: Application):
        """Post initialization hook"""
        # Store components in bot_data
        application.bot_data['db'] = self.db
        application.bot_data['yt_downloader'] = self.yt_downloader
        application.bot_data['ig_downloader'] = self.ig_downloader
        
        logger.info("Bot post-initialization complete")
        
        # Notify admins that bot is online
        for admin_id in ADMIN_IDS:
            try:
                await application.bot.send_message(
                    chat_id=admin_id,
                    text="🤖 <b>Bot is now online!</b>\n\n"
                         "Elite Video Downloader is ready to serve.",
                    parse_mode="HTML"
                )
            except Exception:
                pass
    
    async def post_shutdown(self, application: Application):
        """Post shutdown hook"""
        # Close Instagram downloader session
        if self.ig_downloader:
            await self.ig_downloader.close()
        
        logger.info("Bot shutdown complete")
    
    def setup_handlers(self, application: Application):
        """Register all handlers"""
        
        # Command handlers
        application.add_handler(CommandHandler("start", start_handler))
        application.add_handler(CommandHandler("help", help_handler))
        application.add_handler(CommandHandler("settings", settings_handler))
        application.add_handler(CommandHandler("stats", stats_handler))
        
        # Admin commands
        application.add_handler(CommandHandler("admin", admin_handler))
        application.add_handler(CommandHandler("users", users_handler))
        application.add_handler(CommandHandler("broadcast", broadcast_handler))
        application.add_handler(CommandHandler("ban", ban_handler))
        application.add_handler(CommandHandler("unban", unban_handler))
        application.add_handler(CommandHandler("user_info", user_info_handler))
        application.add_handler(CommandHandler("logs", logs_handler))
        application.add_handler(CommandHandler("maintenance", maintenance_handler))
        
        # Callback query handler
        application.add_handler(CallbackQueryHandler(callback_handler))
        
        # Message handler (for URLs) - must be last
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
        )
        
        # Error handler
        application.add_error_handler(self.error_handler)
        
        logger.info("All handlers registered")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Error: {context.error}", exc_info=True)
        
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ <b>An error occurred.</b>\n"
                    "Please try again or contact support.",
                    parse_mode="HTML"
                )
            except Exception:
                pass
    
    async def cleanup_task(self):
        """Background cleanup task"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                cleanup_old_files(DOWNLOADS_DIR, max_age_hours=1)
                logger.info("Cleanup task completed")
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def run(self):
        """Run the bot"""
        logger.info("Starting Video Downloader Bot...")
        
        # Initialize components
        asyncio.get_event_loop().run_until_complete(self.init_components())
        
        # Build application
        self.application = (
            Application.builder()
            .token(BOT_TOKEN)
            .post_init(self.post_init)
            .post_shutdown(self.post_shutdown)
            .build()
        )
        
        # Setup handlers
        self.setup_handlers(self.application)
        
        logger.info("Bot is starting polling...")
        
        # Run the bot
        self.application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )


def main():
    """Main entry point"""
    bot = VideoDownloaderBot()
    bot.run()


if __name__ == "__main__":
    main()
