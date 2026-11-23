from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest

from database import (
    LOCKS,
    ensure_group,
    get_locks,
    set_lock,
)

from keyboards import locks_keyboard

router = Router(name="locks")


# ==================================================
# TEXT NORMALIZATION
# ==================================================

def normalize_command(text: str) -> str:
    text = text.strip().lower()

    text = text.replace("ي", "ی")
    text = text.replace("ك", "ک")
    text = text.replace("\u200c", " ")

    return " ".join(text.split())


# ==================================================
# GROUP CHECK
# ==================================================

def is_group(message: Message) -> bool:
    return message.chat.type in (
        ChatType.GROUP,
        ChatType.SUPERGROUP
    )


# ==================================================
# ADMIN CHECK
# ==================================================

async def is_group_admin(
    bot,
    chat_id: int,
    user_id: int
) -> bool:

    try:
        member = await bot.get_chat_member(
            chat_id=chat_id,
            user_id=user_id
        )

        return member.status in (
            "administrator",
            "creator"
        )

    except Exception:
        return False


# ==================================================
# PANEL TEXT
# ==================================================

def get_locks_text(locks: dict) -> str:

    enabled_count = sum(
        1 for value in locks.values() if value
    )

    total_count = len(LOCKS)

    return (
        "🔒 <b>پنل مدیریت قفل‌های AZRAEL</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "از دکمه‌های زیر برای مدیریت قفل‌ها استفاده کن.\n\n"
        f"🔒 قفل‌های فعال: <b>{enabled_count}</b>\n"
        f"🔓 قفل‌های باز: <b>{total_count - enabled_count}</b>\n"
        f"📊 مجموع قفل‌ها: <b>{total_count}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🛡 فقط مدیران گروه می‌توانند تنظیمات را تغییر دهند."
    )


# ==================================================
# UPDATE PANEL
# ==================================================

async def update_panel(message: Message, chat_id: int):

    locks = await get_locks(chat_id)

    try:
        await message.edit_text(
            get_locks_text(locks),
            reply_markup=locks_keyboard(locks)
        )

    except TelegramBadRequest as error:

        if "message is not modified" not in str(error).lower():
            raise


# ==================================================
# SHOW LOCK PANEL
# ==================================================

async def show_locks_panel(message: Message):

    if not is_group(message):
        await message.answer(
            "⚠️ پنل قفل‌ها فقط داخل گروه قابل استفاده است."
        )
        return

    if not message.from_user:
        return

    if not await is_group_admin(
        message.bot,
        message.chat.id,
        message.from_user.id
    ):
        await message.answer(
            "⛔ فقط مدیران گروه می‌توانند پنل قفل‌ها را باز کنند."
        )
        return

    await ensure_group(
        message.chat.id,
        message.chat.title or ""
    )

    locks = await get_locks(message.chat.id)

    await message.answer(
        get_locks_text(locks),
        reply_markup=locks_keyboard(locks)
    )


# ==================================================
# /locks COMMAND
# ==================================================

@router.message(Command("locks"))
async def locks_command(message: Message):

    await show_locks_panel(message)


# ==================================================
# PERSIAN LOCK COMMAND
# ==================================================

@router.message(
    F.text.regexp(
        r"^(قفل‌ها|قفل ها|قفلها|قفل|پنل قفل‌ها|پنل قفل ها)$"
    )
)
async def locks_text_command(message: Message):

    await show_locks_panel(message)


# ==================================================
# OPEN LOCK PANEL CALLBACK
# ==================================================

@router.callback_query(F.data == "menu:locks")
async def open_locks_callback(callback: CallbackQuery):

    if not callback.message:
        await callback.answer()
        return

    chat = callback.message.chat

    if chat.type not in (
        ChatType.GROUP,
        ChatType.SUPERGROUP
    ):
        await callback.answer(
            "این پنل فقط داخل گروه قابل استفاده است.",
            show_alert=True
        )
        return

    if not await is_group_admin(
        callback.bot,
        chat.id,
        callback.from_user.id
    ):
        await callback.answer(
            "⛔ فقط مدیران گروه اجازه دسترسی دارند.",
            show_alert=True
        )
        return

    await ensure_group(
        chat.id,
        chat.title or ""
    )

    try:
        await update_panel(
            callback.message,
            chat.id
        )

        await callback.answer()

    except Exception:
        await callback.answer(
            "❌ نمایش پنل ناموفق بود.",
            show_alert=True
        )


# ==================================================
# TOGGLE SINGLE LOCK
# ==================================================

@router.callback_query(F.data.startswith("lock:"))
async def toggle_lock(callback: CallbackQuery):

    if not callback.message:
        await callback.answer()
        return

    chat = callback.message.chat

    if chat.type not in (
        ChatType.GROUP,
        ChatType.SUPERGROUP
    ):
        await callback.answer(
            "این قابلیت فقط داخل گروه فعال است.",
            show_alert=True
        )
        return

    if not await is_group_admin(
        callback.bot,
        chat.id,
        callback.from_user.id
    ):
        await callback.answer(
            "⛔ فقط مدیران گروه اجازه تغییر قفل‌ها را دارند.",
            show_alert=True
        )
        return

    lock_type = callback.data.split(":", 1)[1]

    if lock_type not in LOCKS:
        await callback.answer(
            "❌ قفل موردنظر معتبر نیست.",
            show_alert=True
        )
        return

    try:
        await ensure_group(
            chat.id,
            chat.title or ""
        )

        current_locks = await get_locks(chat.id)

        new_status = not current_locks[lock_type]

        await set_lock(
            chat.id,
            lock_type,
            new_status
        )

        await update_panel(
            callback.message,
            chat.id
        )

        await callback.answer(
            f"{'🔒 قفل شد' if new_status else '🔓 باز شد'}: {LOCKS[lock_type]}"
        )

    except Exception:
        await callback.answer(
            "❌ تغییر وضعیت قفل ناموفق بود.",
            show_alert=True
        )


# ==================================================
# OPEN ALL LOCKS
# ==================================================

@router.callback_query(F.data == "locks:open_all")
async def open_all_locks(callback: CallbackQuery):

    if not callback.message:
        await callback.answer()
        return

    chat = callback.message.chat

    if chat.type not in (
        ChatType.GROUP,
        ChatType.SUPERGROUP
    ):
        await callback.answer(
            "فقط داخل گروه قابل استفاده است.",
            show_alert=True
        )
        return

    if not await is_group_admin(
        callback.bot,
        chat.id,
        callback.from_user.id
    ):
        await callback.answer(
            "⛔ فقط مدیران گروه اجازه دارند.",
            show_alert=True
        )
        return

    try:
        for lock_type in LOCKS:
            await set_lock(
                chat.id,
                lock_type,
                False
            )

        await update_panel(
            callback.message,
            chat.id
        )

        await callback.answer(
            "🔓 تمام قفل‌ها باز شدند."
        )

    except Exception:
        await callback.answer(
            "❌ باز کردن قفل‌ها ناموفق بود.",
            show_alert=True
        )


# ==================================================
# CLOSE ALL LOCKS
# ==================================================

@router.callback_query(F.data == "locks:close_all")
async def close_all_locks(callback: CallbackQuery):

    if not callback.message:
        await callback.answer()
        return

    chat = callback.message.chat

    if chat.type not in (
        ChatType.GROUP,
        ChatType.SUPERGROUP
    ):
        await callback.answer(
            "فقط داخل گروه قابل استفاده است.",
            show_alert=True
        )
        return

    if not await is_group_admin(
        callback.bot,
        chat.id,
        callback.from_user.id
    ):
        await callback.answer(
            "⛔ فقط مدیران گروه اجازه دارند.",
            show_alert=True
        )
        return

    try:
        for lock_type in LOCKS:
            await set_lock(
                chat.id,
                lock_type,
                True
            )

        await update_panel(
            callback.message,
            chat.id
        )

        await callback.answer(
            "🔒 تمام قفل‌ها فعال شدند."
        )

    except Exception:
        await callback.answer(
            "❌ بستن قفل‌ها ناموفق بود.",
            show_alert=True
        )
