from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛡 مدیریت گروه",
                    callback_data="menu:admin"
                ),
                InlineKeyboardButton(
                    text="🔒 قفل‌ها",
                    callback_data="menu:locks"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ تنظیمات",
                    callback_data="menu:settings"
                ),
                InlineKeyboardButton(
                    text="📊 آمار",
                    callback_data="menu:stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎮 سرگرمی",
                    callback_data="menu:games"
                ),
                InlineKeyboardButton(
                    text="📚 راهنما",
                    callback_data="menu:help"
                )
            ]
        ]
    )


def admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔇 سکوت",
                    callback_data="admin:mute"
                ),
                InlineKeyboardButton(
                    text="🔊 لغو سکوت",
                    callback_data="admin:unmute"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⛔ مسدود",
                    callback_data="admin:ban"
                ),
                InlineKeyboardButton(
                    text="✅ رفع مسدودی",
                    callback_data="admin:unban"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚠️ اخطار",
                    callback_data="admin:warn"
                ),
                InlineKeyboardButton(
                    text="🗑 حذف پیام",
                    callback_data="admin:delete"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="menu:home"
                )
            ]
        ]
    )


def locks_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 لینک",
                    callback_data="lock:links"
                ),
                InlineKeyboardButton(
                    text="📷 عکس",
                    callback_data="lock:photos"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎥 ویدیو",
                    callback_data="lock:videos"
                ),
                InlineKeyboardButton(
                    text="🎭 گیف",
                    callback_data="lock:gifs"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎵 موسیقی",
                    callback_data="lock:audio"
                ),
                InlineKeyboardButton(
                    text="📁 فایل",
                    callback_data="lock:files"
                )
            ],
            [
                InlineKeyboardButton(
                    text="😀 استیکر",
                    callback_data="lock:stickers"
                ),
                InlineKeyboardButton(
                    text="🎤 ویس",
                    callback_data="lock:voice"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="menu:home"
                )
            ]
        ]
    )


def back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="menu:home"
                )
            ]
        ]
    )
