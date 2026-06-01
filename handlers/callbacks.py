"""
Callback query handler for inline buttons
"""

import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS, BOT_NAME, ENABLE_STATS
from database import Database
from utils.keyboard import (
    admin_keyboard, settings_keyboard, quality_settings_keyboard,
    format_settings_keyboard, stats_keyboard, confirm_keyboard
)
from utils.helpers import format_file_size, format_duration


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    callback_data = query.data
    
    if callback_data.startswith("dl:"):
        from handlers.download import url_handler
        await url_handler(update, context)
        return
    
    elif callback_data.startswith("admin:"):
        if user.id not in ADMIN_IDS:
            await query.edit_message_text("❌ <b>Not authorized!</b>", parse_mode="HTML")
            return
        await handle_admin_callbacks(update, context, callback_data)
        return
    
    elif callback_data.startswith("settings:"):
        await handle_settings_callbacks(update, context, callback_data)
        return
    
    elif callback_data.startswith("set_quality:"):
        await handle_quality_setting(update, context, callback_data)
        return
    
    elif callback_data.startswith("set_format:"):
        await handle_format_setting(update, context, callback_data)
        return
    
    elif callback_data.startswith("stats:"):
        await handle_stats_callback(update, context, callback_data)
        return
    
    elif callback_data.startswith("confirm:"):
        await handle_confirm_callback(update, context, callback_data)
        return


async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Handle admin panel callbacks"""
    query = update.callback_query
    action = callback_data.split(":")[1]
    db: Database = context.bot_data.get('db')
    
    if action == "stats":
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
        await query.edit_message_text(stats_text, parse_mode="HTML")
        await query.message.reply_text("👑 <b>Admin Panel</b>", parse_mode="HTML", reply_markup=admin_keyboard())
    
    elif action == "users":
        users = db.get_all_users()
        if users:
            text = f"👥 <b>Total Users: {len(users)}</b>\n\n"
            for u in users[:50]:
                name = u.first_name or u.username or "Unknown"
                banned = "🚫" if u.is_banned else "✅"
                text += f"{banned} <code>{u.user_id}</code> - {name}\n"
        else:
            text = "No users found."
        await query.edit_message_text(text, parse_mode="HTML")
        await query.message.reply_text("👑 <b>Admin Panel</b>", parse_mode="HTML", reply_markup=admin_keyboard())
    
    elif action == "broadcast":
        await query.edit_message_text(
            "📢 <b>Broadcast</b>\n\n"
            "Use command:\n"
            "/broadcast &lt;your message&gt;\n\n"
            "Example: /broadcast Hello everyone!",
            parse_mode="HTML"
        )
        await query.message.reply_text("👑 <b>Admin Panel</b>", parse_mode="HTML", reply_markup=admin_keyboard())
    
    elif action == "maintenance":
        import config
        status = "ON" if config.maintenance_mode else "OFF"
        await query.edit_message_text(
            f"🔧 <b>Maintenance Mode: {status}</b>\n\n"
            "Use command:\n"
            "/maintenance on - Enable\n"
            "/maintenance off - Disable",
            parse_mode="HTML"
        )
        await query.message.reply_text("👑 <b>Admin Panel</b>", parse_mode="HTML", reply_markup=admin_keyboard())
    
    elif action == "logs":
        from handlers.admin import logs_handler
        # Create a fake update with message
        await query.edit_message_text("📋 Check logs with /logs command.", parse_mode="HTML")
        await query.message.reply_text("👑 <b>Admin Panel</b>", parse_mode="HTML", reply_markup=admin_keyboard())


async def handle_settings_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Handle settings navigation callbacks"""
    query = update.callback_query
    action = callback_data.split(":")[1]
    
    if action == "quality":
        await query.edit_message_text(
            "🎯 <b>Select Default Quality:</b>\n\n"
            "This will be your default when downloading videos.",
            parse_mode="HTML",
            reply_markup=quality_settings_keyboard()
        )
    
    elif action == "format":
        await query.edit_message_text(
            "📁 <b>Select Preferred Format:</b>\n\n"
            "Video - Download as video file\n"
            "Audio - Download audio only (MP3)",
            parse_mode="HTML",
            reply_markup=format_settings_keyboard()
        )
    
    elif action == "stats":
        db: Database = context.bot_data.get('db')
        user_data = db.get_user(query.from_user.id)
        
        if user_data:
            downloads = db.get_user_downloads(query.from_user.id, limit=5)
            text = (
                f"📊 <b>Your Statistics</b>\n\n"
                f"⬇️ Total Downloads: {user_data.total_downloads}\n"
                f"⚙️ Default Quality: {user_data.default_quality}p\n"
                f"📁 Preferred Format: {user_data.preferred_format.capitalize()}\n"
            )
            if downloads:
                text += "\n<b>Recent:</b>\n"
                for dl in downloads[:5]:
                    status = "✅" if dl.status == "completed" else "❌"
                    text += f"{status} {dl.title[:30]}...\n"
        else:
            text = "No data found."
        
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=stats_keyboard())
    
    elif action == "back":
        db: Database = context.bot_data.get('db')
        user_data = db.get_user(query.from_user.id)
        
        settings_text = (
            f"⚙️ <b>Your Settings</b>\n\n"
            f"🎯 <b>Default Quality:</b> {user_data.default_quality if user_data else '720'}p\n"
            f"📁 <b>Preferred Format:</b> {(user_data.preferred_format if user_data else 'video').capitalize()}\n\n"
            f"Select an option:"
        )
        await query.edit_message_text(
            settings_text,
            parse_mode="HTML",
            reply_markup=settings_keyboard()
        )


async def handle_quality_setting(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Handle quality preference change"""
    query = update.callback_query
    quality = callback_data.split(":")[1]
    
    db: Database = context.bot_data.get('db')
    db.update_user_settings(query.from_user.id, quality=quality)
    
    await query.answer(f"✅ Default quality set to {quality}p")
    
    # Go back to settings
    await handle_settings_callbacks(update, context, "settings:back")


async def handle_format_setting(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Handle format preference change"""
    query = update.callback_query
    fmt = callback_data.split(":")[1]
    
    db: Database = context.bot_data.get('db')
    db.update_user_settings(query.from_user.id, format_pref=fmt)
    
    await query.answer(f"✅ Preferred format set to {fmt}")
    
    # Go back to settings
    await handle_settings_callbacks(update, context, "settings:back")


async def handle_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Handle stats refresh"""
    query = update.callback_query
    await handle_settings_callbacks(update, context, "settings:stats")


async def handle_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Handle confirmation callbacks"""
    query = update.callback_query
    parts = callback_data.split(":")
    action = parts[1]
    choice = parts[2]
    
    if action == "broadcast" and choice == "yes":
        message = context.user_data.get('broadcast_message', '')
        if message:
            await query.edit_message_text("📢 <b>Broadcasting...</b>", parse_mode="HTML")
            
            db: Database = context.bot_data.get('db')
            users = db.get_all_users()
            
            sent = 0
            failed = 0
            
            for user in users:
                try:
                    await context.bot.send_message(
                        chat_id=user.user_id,
                        text=f"📢 <b>Announcement</b>\n\n{message}",
                        parse_mode="HTML"
                    )
                    sent += 1
                    await asyncio.sleep(0.05)  # Rate limit
                except Exception:
                    failed += 1
            
            await query.edit_message_text(
                f"✅ <b>Broadcast complete!</b>\n\n"
                f"Sent: {sent}\n"
                f"Failed: {failed}",
                parse_mode="HTML"
            )
            
            if 'broadcast_message' in context.user_data:
                del context.user_data['broadcast_message']
    
    elif action == "broadcast" and choice == "no":
        await query.edit_message_text("❌ <b>Broadcast cancelled.</b>", parse_mode="HTML")
        if 'broadcast_message' in context.user_data:
            del context.user_data['broadcast_message']
