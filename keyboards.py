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
    def toggle_btn(key, label):
        # دکمه‌ای که وضعیت فعلی را نشان می‌دهد و با کلیک تغییر می‌کند
        status = "✅" if settings.get(key) else "❌"
        return InlineKeyboardButton(f"{status} {label}", callback_data=f"toggle_{key}")

    keyboard = [
        [toggle_btn('lock_link', 'لینک'), toggle_btn('lock_forward', 'فوروارد')],
        [toggle_btn('lock_sticker', 'استیکر'), toggle_btn('lock_gif', 'گیف')],
        [toggle_btn('lock_photo', 'عکس'), toggle_btn('lock_video', 'ویدیو')],
        [toggle_btn('lock_file', 'فایل'), toggle_btn('lock_voice', 'پیام صوتی')],
        [toggle_btn('lock_username', 'یوزرنیم'), toggle_btn('lock_hashtag', 'هشتگ')],
        [toggle_btn('lock_bots', 'ربات‌ها'), toggle_btn('lock_emoji', 'ایموجی')],
        [toggle_btn('lock_poll', 'نظرسنجی'), toggle_btn('lock_contact', 'مخاطب')],
        [toggle_btn('lock_location', 'موقعیت'), toggle_btn('lock_game', 'بازی')],
        [toggle_btn('lock_audio', 'صدا'), toggle_btn('lock_video_note', 'ویدیو نوت')],
        [toggle_btn('lock_voice_chat', 'وییس چت'), toggle_btn('lock_caption', 'کپشن')],
        [toggle_btn('anti_flood', 'ضد اسپم'), toggle_btn('anti_repeat', 'ضد تکرار')],
        [toggle_btn('anti_bad_words', 'کلمات رکیک'), toggle_btn('anti_spam', 'ضد تبلیغ')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="panel_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def welcome_panel(settings):
    status = "✅ فعال" if settings['welcome_enabled'] else "❌ غیرفعال"
    keyboard = [
        [InlineKeyboardButton(f"{status} (کلیک کنید)", callback_data="toggle_welcome_enabled")],
        [InlineKeyboardButton("📝 تغییر متن خوش‌آمدگویی", callback_data="change_welcome_text")],
        [InlineKeyboardButton("⏱ حذف خودکار پس از ۶۰ ثانیه", callback_data="toggle_auto_delete_welcome")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="panel_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def help_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 کپی دستور اخطار", copy_text=CopyTextButton(text="/اخطار"))],
        [InlineKeyboardButton("📋 کپی دستور سکوت موقت", copy_text=CopyTextButton(text="/سکوت_موقت 1h"))],
        [InlineKeyboardButton("📋 کپی دستور پاکسازی", copy_text=CopyTextButton(text="/پاکسازی"))],
        [InlineKeyboardButton("📋 کپی دستور خوش‌آمد", copy_text=CopyTextButton(text="/تنظیم_خوشامد سلام {name}"))],
        [InlineKeyboardButton("📋 کپی دستور حداکثر اخطار", copy_text=CopyTextButton(text="/حداکثر_اخطار 3"))],
    ]
    return InlineKeyboardMarkup(keyboard)
