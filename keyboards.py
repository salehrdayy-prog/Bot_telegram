from telegram import InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton

def main_panel():
    keyboard = [
        [InlineKeyboardButton("🔒 قفل‌ها", callback_data="panel_locks")],
        [InlineKeyboardButton("⚠️ سیستم اخطار", callback_data="panel_warns")],
        [InlineKeyboardButton("👋 خوش‌آمدگویی", callback_data="panel_welcome")],
        [InlineKeyboardButton("🧹 پاکسازی گروه", callback_data="panel_purge")],
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
        [InlineKeyboardButton(f"{status('lock_username')} یوزرنیم", callback_data="toggle_lock_lock_username"),
         InlineKeyboardButton(f"{status('lock_hashtag')} هشتگ", callback_data="toggle_lock_lock_hashtag")],
        [InlineKeyboardButton(f"{status('lock_bots')} ربات‌ها", callback_data="toggle_lock_lock_bots"),
         InlineKeyboardButton(f"{status('lock_emoji')} ایموجی", callback_data="toggle_lock_lock_emoji")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="panel_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def welcome_panel(settings):
    status = "✅ فعال" if settings['welcome_enabled'] else "❌ غیرفعال"
    keyboard = [
        [InlineKeyboardButton(f"وضعیت: {status}", callback_data="toggle_welcome")],
        [InlineKeyboardButton("📝 تغییر متن خوش‌آمدگویی", callback_data="change_welcome_text")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="panel_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

# کیبورد جدید برای راهنما (دکمه‌های کپی)
def help_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 کپی دستور اخطار", copy_text=CopyTextButton(text="/warn"))],
        [InlineKeyboardButton("📋 کپی دستور سکوت موقت", copy_text=CopyTextButton(text="/mutetime 1h"))],
        [InlineKeyboardButton("📋 کپی دستور پاکسازی", copy_text=CopyTextButton(text="/purge"))],
        [InlineKeyboardButton("📋 کپی دستور تغییر متن خوش‌آمد", copy_text=CopyTextButton(text="/setwelcome سلام {name} عزیز"))],
        [InlineKeyboardButton("📋 کپی دستور تنظیم اخطار", copy_text=CopyTextButton(text="/setmaxwarns 3"))],
    ]
    return InlineKeyboardMarkup(keyboard)
