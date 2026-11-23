from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType

from database import LOCKS, ensure_group, get_locks, set_lock
from keyboards import locks_keyboard

router = Router()


# ==================================================
# TEXT NORMALIZATION
# ==================================================

def normalize_command(text: str) -> str:
    text = text.strip().lower()

    text = text.replace("ي", "ی")
    text = text.replace("ك", "ک")
    text = text.replace("\u200c", " ")
    text = " ".join(text.split())

    return text


# ==================================================
# CHECK ADMIN
# ==================================================

async def is_group_admin(bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(
            chat_id=chat_id,
            user_id=user_id
        )

        return member.status in ("administrator", "creator")

    except Exception:
        return False


# ==================================================
# PANEL TEXT
# ==================================================

def get_locks_text(locks: dict) -> str:
    enabled_count = sum(1 for value in locks.values() if value)
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
# SHOW PANEL
# ==================================================

async def show_locks_panel(message: Message):

    if message.chat.type not in (
        ChatType.GROUP,
        ChatType.SUPERGROUP
    ):
        await message.answer(
            "⚠️ این دستور فقط داخل گروه قابل استفاده است."
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
            "⛔ فقط مدیران گروه اجازه دسترسی دارند."
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
# LOCK COMMANDS
# ==================================================

@router.message(F.text)
async def locks_text_handler(message: Message):

    if not message.text:
        return

    text = normalize_command(message.text)

    # پشتیبانی از /locks و /locks@BotUsername
    command = text.split()[0].split("@")[0]

    if command == "/locks":
        await show_locks_panel(message)
        return

    # پشتیبانی از شکل‌های مختلف فارسی
    if text in {
        "قفل ها",
        "قفلها",
        "پنل قفل ها",
        "قفل",
    }:
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

    await ensure_group(chat.id, chat.title or "")

    locks = await get_locks(chat.id)

    await callback.message.edit_text(
        get_locks_text(locks),
        reply_markup=locks_keyboard(locks)
    )

    await callback.answer()


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
            "❌ قفل نامعتبر است.",
            show_alert=True
        )
        return

    await ensure_group(chat.id, chat.title or "")

    current_locks = await get_locks(chat.id)
    new_status = not current_locks[lock_type]

    await set_lock(
        chat.id,
        lock_type,
        new_status
    )

    updated_locks = await get_locks(chat.id)

    await callback.message.edit_text(
        get_locks_text(updated_locks),
        reply_markup=locks_keyboard(updated_locks)
    )

    await callback.answer(
        f"{'🔒 قفل شد' if new_status else '🔓 باز شد'}: {LOCKS[lock_type]}"
    )


# ==================================================
# OPEN ALL
# ==================================================

@router.callback_query(F.data == "locks:open_all")
async def open_all_locks(callback: CallbackQuery):

    if not callback.message:
        await callback.answer()
        return

    chat = callback.message.chat

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

    for lock_type in LOCKS:
        await set_lock(chat.id, lock_type, False)

    locks = await get_locks(chat.id)

    await callback.message.edit_text(
        get_locks_text(locks),
        reply_markup=locks_keyboard(locks)
    )

    await callback.answer("🔓 تمام قفل‌ها باز شدند.")


# ==================================================
# CLOSE ALL
# ==================================================

@router.callback_query(F.data == "locks:close_all")
async def close_all_locks(callback: CallbackQuery):

    if not callback.message:
        await callback.answer()
        return

    chat = callback.message.chat

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

    for lock_type in LOCKS:
        await set_lock(chat.id, lock_type, True)

    locks = await get_locks(chat.id)

    await callback.message.edit_text(
        get_locks_text(locks),
        reply_markup=locks_keyboard(locks)
    )

    await callback.answer("🔒 تمام قفل‌ها فعال شدند.")
