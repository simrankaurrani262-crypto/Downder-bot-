"""
Start and Help command handlers
"""

from telegram import Update
from telegram.ext import ContextTypes
from config import BOT_NAME, WELCOME_MESSAGE, HELP_MESSAGE, ADMIN_IDS
from database import Database
from database.models import User


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Register user in database
    db: Database = context.bot_data.get('db')
    if db:
        new_user = User(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
        )
        is_new = db.add_user(new_user)
        db.update_user_activity(user.id)
    
    welcome_text = WELCOME_MESSAGE.format(bot_name=BOT_NAME)
    
    if is_new:
        welcome_text += "\n🎉 <b>Welcome! You're now registered.</b>"
    
    # Check if user is admin
    if user.id in ADMIN_IDS:
        welcome_text += "\n\n👑 <b>You have admin privileges.</b>\nUse /admin for admin panel."
    
    await update.message.reply_text(welcome_text, parse_mode="HTML")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user = update.effective_user
    help_text = HELP_MESSAGE
    
    # Add admin help if applicable
    if user.id in ADMIN_IDS:
        from config import ADMIN_HELP
        help_text += "\n\n" + ADMIN_HELP
    
    await update.message.reply_text(help_text, parse_mode="HTML")
