"""
Settings command handler
User preferences and configuration
"""

from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from utils.keyboard import settings_keyboard, quality_settings_keyboard, format_settings_keyboard


async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    user = update.effective_user
    db: Database = context.bot_data.get('db')
    
    if not db:
        await update.message.reply_text("❌ Database not available.", parse_mode="HTML")
        return
    
    user_data = db.get_user(user.id)
    
    if not user_data:
        await update.message.reply_text(
            "⚙️ <b>Settings</b>\n\nPlease use /start first to register.",
            parse_mode="HTML"
        )
        return
    
    settings_text = (
        f"⚙️ <b>Your Settings</b>\n\n"
        f"🎯 <b>Default Quality:</b> {user_data.default_quality}p\n"
        f"📁 <b>Preferred Format:</b> {user_data.preferred_format.capitalize()}\n\n"
        f"Select an option to change:"
    )
    
    await update.message.reply_text(
        settings_text,
        parse_mode="HTML",
        reply_markup=settings_keyboard(
            current_quality=user_data.default_quality,
            current_format=user_data.preferred_format
        )
    )
