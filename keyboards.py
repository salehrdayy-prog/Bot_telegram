from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_panel():
    keyboard = [
        [InlineKeyboardButton("🔒 قفل‌ها", callback_data="panel_locks")],
        [InlineKeyboardButton("⚠️ سیستم اخطار", callback_data="panel_warns")],
        [InlineKeyboardButton("👋 خوش‌آمدگویی", callback_data="panel_welcome")],
    ]
    return InlineKeyboardMarkup(keyboard)

def locks_panel(settings):
    def status(key):
        return "✅" if settings.get(key) else "❌"
    
    keyboard = [
        [InlineKeyboardButton(f"{status('lock_link')} لینک", callback_data="toggle_lock_lock_link"),
         InlineKeyboardButton(f"{status('lock_forward')} فوروارد", callback_data="toggle_lock_lock_forward")],
        [InlineKeyboardButton(f"{status('lock_sticker')} استیکر", callback_data="toggle_lock_lock_sticker"),
         InlineKeyboardButton(f"{status('lock_gif')} گیف", callback_data="toggle_lock_lock_gif")],
        [InlineKeyboardButton(f"{status('lock_photo')} عکس", callback_data="toggle_lock_lock_photo"),
         InlineKeyboardButton(f"{status('lock_video')} ویدیو", callback_data="toggle_lock_lock_video")],
        [InlineKeyboardButton(f"{status('lock_file')} فایل", callback_data="toggle_lock_lock_file"),
         InlineKeyboardButton(f"{status('lock_voice')} پیام صوتی", callback_data="toggle_lock_lock_voice")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="panel_main")],
    ]
    return InlineKeyboardMarkup(keyboard)
