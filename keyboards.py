from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ==================================================
# MAIN MENU
# ==================================================

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


# ==================================================
# ADMIN PANEL
# ==================================================

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


# ==================================================
# LOCKS
# ==================================================

LOCK_BUTTONS = [
    ("links", "🔗 لینک‌ها"),
    ("forwards", "↪️ فوروارد"),
    ("text", "📝 متن"),
    ("hashtags", "#️⃣ هشتگ"),
    ("mentions", "📢 منشن"),
    ("phone_numbers", "📱 شماره تلفن"),
    ("emojis", "😀 ایموجی"),
    ("photos", "📷 عکس"),
    ("videos", "🎥 ویدیو"),
    ("gifs", "🎭 گیف"),
    ("stickers", "🎨 استیکر"),
    ("voice", "🎤 ویس"),
    ("video_notes", "⭕ ویدیو مسیج"),
    ("audio", "🎵 موسیقی"),
    ("files", "📁 فایل"),
    ("contacts", "👤 مخاطبین"),
    ("locations", "📍 موقعیت مکانی"),
    ("polls", "📊 نظرسنجی"),
    ("bots", "🤖 پیام ربات‌ها"),
    ("new_members", "👥 ورود اعضا"),
    ("group_info", "⚙️ تغییرات گروه"),
    ("group_photo", "🖼 عکس گروه"),
    ("poll_creation", "📋 ساخت نظرسنجی"),
    ("service_messages", "🔔 پیام سیستمی"),
]


def locks_keyboard(locks=None):
    """
    ساخت پنل ۲۴ قفل.

    locks:
        دیکشنری وضعیت قفل‌ها از تابع get_locks

    اگر وضعیت ارسال نشود، تمام قفل‌ها باز نمایش داده می‌شوند.
    """

    if locks is None:
        locks = {}

    keyboard = []

    for index in range(0, len(LOCK_BUTTONS), 2):

        row = []

        for lock_key, lock_title in LOCK_BUTTONS[index:index + 2]:

            enabled = bool(locks.get(lock_key, False))

            status = "🔒" if enabled else "🔓"

            row.append(
                InlineKeyboardButton(
                    text=f"{status} {lock_title}",
                    callback_data=f"lock:{lock_key}"
                )
            )

        keyboard.append(row)

    # باز کردن تمام قفل‌ها
    keyboard.append([
        InlineKeyboardButton(
            text="🔓 باز کردن همه قفل‌ها",
            callback_data="locks:open_all"
        )
    ])

    # بستن تمام قفل‌ها
    keyboard.append([
        InlineKeyboardButton(
            text="🔒 بستن همه قفل‌ها",
            callback_data="locks:close_all"
        )
    ])

    # بازگشت به منوی اصلی
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="menu:home"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


# ==================================================
# BACK BUTTON
# ==================================================

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
