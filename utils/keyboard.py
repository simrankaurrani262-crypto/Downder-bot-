"""
Inline keyboard builders for the bot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import QUALITY_PRESETS
from utils.helpers import get_quality_label


def quality_selection_keyboard(platform: str, is_youtube: bool = True) -> InlineKeyboardMarkup:
    """Create quality selection keyboard"""
    buttons = []
    
    if is_youtube:
        # Audio option first
        buttons.append([
            InlineKeyboardButton("🎵 Audio Only (MP3)", callback_data=f"dl:audio")
        ])
        
        # Quality rows
        qualities = [
            ["144", "240", "360"],
            ["480", "720", "1080"],
            ["1440", "2160", "best"],
        ]
        
        for row in qualities:
            button_row = []
            for q in row:
                label = get_quality_label(q)
                button_row.append(InlineKeyboardButton(label, callback_data=f"dl:{q}"))
            buttons.append(button_row)
    else:
        # Instagram - usually best quality
        buttons.append([
            InlineKeyboardButton("📥 Best Quality", callback_data="dl:best"),
        ])
        buttons.append([
            InlineKeyboardButton("🎵 Audio Only", callback_data="dl:audio"),
        ])
    
    buttons.append([
        InlineKeyboardButton("❌ Cancel", callback_data="dl:cancel")
    ])
    
    return InlineKeyboardMarkup(buttons)


def settings_keyboard(current_quality: str = "720", current_format: str = "video") -> InlineKeyboardMarkup:
    """Create settings keyboard"""
    buttons = [
        [InlineKeyboardButton("⚙️ Default Quality", callback_data="settings:quality")],
        [InlineKeyboardButton("📁 Preferred Format", callback_data="settings:format")],
        [InlineKeyboardButton("📊 My Stats", callback_data="settings:stats")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings:back")],
    ]
    return InlineKeyboardMarkup(buttons)


def quality_settings_keyboard() -> InlineKeyboardMarkup:
    """Create quality settings keyboard"""
    buttons = []
    qualities = [
        ["360", "720", "1080"],
        ["1440", "2160", "best"],
    ]
    for row in qualities:
        button_row = []
        for q in row:
            label = get_quality_label(q)
            button_row.append(InlineKeyboardButton(label, callback_data=f"set_quality:{q}"))
        buttons.append(button_row)
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="settings:back")])
    return InlineKeyboardMarkup(buttons)


def format_settings_keyboard() -> InlineKeyboardMarkup:
    """Create format preference keyboard"""
    buttons = [
        [InlineKeyboardButton("📹 Video", callback_data="set_format:video")],
        [InlineKeyboardButton("🎵 Audio Only", callback_data="set_format:audio")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings:back")],
    ]
    return InlineKeyboardMarkup(buttons)


def admin_keyboard() -> InlineKeyboardMarkup:
    """Create admin panel keyboard"""
    buttons = [
        [InlineKeyboardButton("📊 Statistics", callback_data="admin:stats")],
        [InlineKeyboardButton("👥 Users", callback_data="admin:users")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin:broadcast")],
        [InlineKeyboardButton("🔧 Maintenance", callback_data="admin:maintenance")],
        [InlineKeyboardButton("📋 Logs", callback_data="admin:logs")],
    ]
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """Create confirmation keyboard"""
    buttons = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm:{action}:yes"),
            InlineKeyboardButton("❌ No", callback_data=f"confirm:{action}:no"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def cancel_keyboard() -> InlineKeyboardMarkup:
    """Simple cancel keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel Download", callback_data="dl:cancel")]
    ])


def stats_keyboard() -> InlineKeyboardMarkup:
    """Stats navigation keyboard"""
    buttons = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="stats:refresh")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings:back")],
    ]
    return InlineKeyboardMarkup(buttons)
