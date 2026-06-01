"""
Admin command handlers
Admin panel, statistics, broadcast, user management
"""

import os
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS, BOT_NAME
from database import Database
from database.models import BotStats
from utils.keyboard import admin_keyboard, confirm_keyboard


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - Show admin panel"""
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ <b>You are not authorized!</b>", parse_mode="HTML")
        return
    
    stats = get_quick_stats(context)
    
    admin_text = (
        f"👑 <b>Admin Panel</b> - {BOT_NAME}\n\n"
        f"📊 <b>Quick Stats:</b>\n"
        f"• Users: {stats['users']}\n"
        f"• Downloads: {stats['downloads']}\n"
        f"• Today Active: {stats['active_today']}\n\n"
        f"Select an option below:"
    )
    
    await update.message.reply_text(
        admin_text,
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user = update.effective_user
    db: Database = context.bot_data.get('db')
    
    if not db:
        await update.message.reply_text("❌ Database not available.", parse_mode="HTML")
        return
    
    # Admin stats
    if is_admin(user.id) and context.args and context.args[0] == "all":
        stats = db.get_bot_stats()
        
        stats_text = (
            f"📊 <b>Bot Statistics</b>\n\n"
            f"👥 <b>Users:</b>\n"
            f"• Total: {stats.total_users:,}\n"
            f"• Active Today: {stats.active_today:,}\n"
            f"• Active This Week: {stats.active_week:,}\n\n"
            f"⬇️ <b>Downloads:</b>\n"
            f"• Total: {stats.total_downloads:,}\n"
            f"• YouTube: {stats.youtube_downloads:,}\n"
            f"• Instagram: {stats.instagram_downloads:,}\n"
            f"• Failed: {stats.failed_downloads:,}\n"
            f"• Avg Time: {stats.avg_download_time}s\n\n"
            f"🤖 <b>Bot:</b> {BOT_NAME}"
        )
        
        await update.message.reply_text(stats_text, parse_mode="HTML")
    
    else:
        # User personal stats
        user_data = db.get_user(user.id)
        if user_data:
            downloads = db.get_user_downloads(user.id, limit=5)
            
            stats_text = (
                f"📊 <b>Your Statistics</b>\n\n"
                f"⬇️ <b>Total Downloads:</b> {user_data.total_downloads}\n"
                f"⚙️ <b>Default Quality:</b> {user_data.default_quality}p\n"
                f"📁 <b>Preferred Format:</b> {user_data.preferred_format.capitalize()}\n\n"
            )
            
            if downloads:
                stats_text += "<b>Recent Downloads:</b>\n"
                for i, dl in enumerate(downloads[:5], 1):
                    status_icon = "✅" if dl.status == "completed" else "❌"
                    platform_icon = "📹" if dl.platform == "youtube" else "📸"
                    title = (dl.title[:30] + "...") if len(dl.title) > 30 else dl.title
                    stats_text += f"{i}. {status_icon} {platform_icon} {title}\n"
            
            await update.message.reply_text(stats_text, parse_mode="HTML")
        else:
            await update.message.reply_text(
                "📊 <b>No statistics yet.</b>\nStart downloading to see your stats!",
                parse_mode="HTML"
            )


async def users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /users command - List all users (admin only)"""
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ <b>Not authorized!</b>", parse_mode="HTML")
        return
    
    db: Database = context.bot_data.get('db')
    if not db:
        await update.message.reply_text("❌ Database not available.", parse_mode="HTML")
        return
    
    users = db.get_all_users()
    
    if not users:
        await update.message.reply_text("No users found.", parse_mode="HTML")
        return
    
    # Send users in batches
    batch_size = 20
    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        text = f"👥 <b>Users ({i+1}-{min(i+len(batch), len(users))} of {len(users)}):</b>\n\n"
        
        for u in batch:
            name = u.first_name or u.username or "Unknown"
            username_text = f"@{u.username}" if u.username else "No username"
            banned = "🚫" if u.is_banned else "✅"
            text += f"{banned} <code>{u.user_id}</code> - {name} ({username_text})\n"
        
        await update.message.reply_text(text, parse_mode="HTML")


async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command - Send message to all users (admin only)"""
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ <b>Not authorized!</b>", parse_mode="HTML")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📢 <b>Broadcast Usage:</b>\n"
            "/broadcast &lt;message&gt;\n\n"
            "Example:\n"
            '/broadcast Hello everyone! New update available.',
            parse_mode="HTML"
        )
        return
    
    message = " ".join(context.args)
    db: Database = context.bot_data.get('db')
    
    if not db:
        await update.message.reply_text("❌ Database not available.", parse_mode="HTML")
        return
    
    # Confirm broadcast
    users = db.get_all_users()
    await update.message.reply_text(
        f"📢 <b>Broadcast to {len(users)} users?</b>\n\n"
        f"Message:\n<code>{message[:500]}</code>",
        parse_mode="HTML",
        reply_markup=confirm_keyboard("broadcast")
    )
    
    # Store message for confirmation
    context.user_data['broadcast_message'] = message


async def ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ban command"""
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ <b>Not authorized!</b>", parse_mode="HTML")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /ban &lt;user_id&gt;", parse_mode="HTML")
        return
    
    try:
        target_id = int(context.args[0])
        db: Database = context.bot_data.get('db')
        
        if db.ban_user(target_id):
            await update.message.reply_text(
                f"🚫 <b>User {target_id} has been banned.</b>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("❌ Failed to ban user.", parse_mode="HTML")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.", parse_mode="HTML")


async def unban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unban command"""
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ <b>Not authorized!</b>", parse_mode="HTML")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /unban &lt;user_id&gt;", parse_mode="HTML")
        return
    
    try:
        target_id = int(context.args[0])
        db: Database = context.bot_data.get('db')
        
        if db.unban_user(target_id):
            await update.message.reply_text(
                f"✅ <b>User {target_id} has been unbanned.</b>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("❌ Failed to unban user.", parse_mode="HTML")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.", parse_mode="HTML")


async def user_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /user_info command"""
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ <b>Not authorized!</b>", parse_mode="HTML")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /user_info &lt;user_id&gt;", parse_mode="HTML")
        return
    
    try:
        target_id = int(context.args[0])
        db: Database = context.bot_data.get('db')
        target_user = db.get_user(target_id)
        
        if target_user:
            text = (
                f"👤 <b>User Info</b>\n\n"
                f"ID: <code>{target_user.user_id}</code>\n"
                f"Username: @{target_user.username or 'N/A'}\n"
                f"Name: {target_user.first_name or ''} {target_user.last_name or ''}\n"
                f"Downloads: {target_user.total_downloads}\n"
                f"Joined: {target_user.joined_date[:10]}\n"
                f"Last Active: {target_user.last_activity[:10]}\n"
                f"Banned: {'Yes' if target_user.is_banned else 'No'}"
            )
            await update.message.reply_text(text, parse_mode="HTML")
        else:
            await update.message.reply_text("User not found.", parse_mode="HTML")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.", parse_mode="HTML")


async def logs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /logs command"""
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ <b>Not authorized!</b>", parse_mode="HTML")
        return
    
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'bot.log')
    
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                # Get last 50 lines
                lines = f.readlines()
                last_lines = lines[-50:] if len(lines) > 50 else lines
                log_text = ''.join(last_lines)
            
            if len(log_text) > 4000:
                log_text = log_text[-4000:]
            
            await update.message.reply_text(
                f"<b>Last 50 log lines:</b>\n<pre>{log_text}</pre>",
                parse_mode="HTML"
            )
        except Exception as e:
            await update.message.reply_text(f"Error reading logs: {e}", parse_mode="HTML")
    else:
        await update.message.reply_text("No log file found.", parse_mode="HTML")


async def maintenance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /maintenance command"""
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ <b>Not authorized!</b>", parse_mode="HTML")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /maintenance &lt;on/off&gt;\nExample: /maintenance on",
            parse_mode="HTML"
        )
        return
    
    status = context.args[0].lower()
    import config
    
    if status == "on":
        config.maintenance_mode = True
        await update.message.reply_text(
            "🔧 <b>Maintenance mode ENABLED.</b>\n"
            "Users will see a maintenance message.",
            parse_mode="HTML"
        )
    elif status == "off":
        config.maintenance_mode = False
        await update.message.reply_text(
            "✅ <b>Maintenance mode DISABLED.</b>\n"
            "Bot is back to normal operation.",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("Usage: /maintenance &lt;on/off&gt;", parse_mode="HTML")


def get_quick_stats(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Get quick stats for admin panel"""
    db: Database = context.bot_data.get('db')
    if db:
        stats = db.get_bot_stats()
        return {
            'users': stats.total_users,
            'downloads': stats.total_downloads,
            'active_today': stats.active_today,
        }
    return {'users': 0, 'downloads': 0, 'active_today': 0}
