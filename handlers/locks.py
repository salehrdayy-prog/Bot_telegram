import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest

from database import LOCKS, ensure_group, get_locks, set_lock
from keyboards import locks_keyboard

router = Router(name="locks")
logger = logging.getLogger("AZRAEL.LOCKS")


# ==================================================
# NORMALIZATION
# ==================================================

def normalize_command(text: str) -> str:
    text = text.strip().lower()
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = text.replace("\u200c", " ")
    return " ".join(text.split())


# ==================================================
# ADMIN CHECK
# ==================================================

async def is_group_admin(bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        logger.exception("Admin check failed | chat=%s user=%s", chat_id, user_id)
        return False


# ==================================================
# PANEL TEXT
# ==================================================

def get_locks_text(locks: dict) -> str:
    active = sum(bool(v) for v in locks.values())
    total = len(LOCKS)

    return (
        "🔒 <b>پنل مدیریت قفل‌های AZRAEL</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "از دکمه‌های زیر برای مدیریت قفل‌ها استفاده کن.\n\n"
        f"🔒 قفل‌های فعال: <b>{active}</b>\n"
        f"🔓 قفل‌های باز: <b>{total - active}</b>\n"
        f"📊 مجموع قفل‌ها: <b>{total}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🛡 فقط مدیران گروه می‌توانند تنظیمات را تغییر دهند."
    )


# ==================================================
# PANEL UPDATE
# ==================================================

async def update_panel(message: Message, chat_id: int):
    logger.info("Updating panel | chat=%s", chat_id)

    locks = await get_locks(chat_id)

    try:
        await message.edit_text(
            get_locks_text(locks),
            reply_markup=locks_keyboard(locks)
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise


# ==================================================
# SHOW PANEL
# ==================================================

async def show_locks_panel(message: Message):
    logger.info(
        "show_locks_panel entered | chat=%s | user=%s",
        message.chat.id,
        message.from_user.id if message.from_user else None
    )

    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await message.answer("⚠️ این دستور فقط داخل گروه قابل استفاده است.")
        logger.info("Rejected: not a group")
        return

    if not message.from_user:
        logger.warning("Rejected: message has no from_user")
        return

    admin = await is_group_admin(
        message.bot, message.chat.id, message.from_user.id
    )

    logger.info("Admin check result: %s", admin)

    if not admin:
        await message.answer("⛔ فقط مدیران گروه می‌توانند پنل قفل‌ها را باز کنند.")
        return

    await ensure_group(message.chat.id, message.chat.title or "")
    logger.info("Group ensured")

    locks = await get_locks(message.chat.id)
    logger.info("Locks loaded: %s", locks)

    await message.answer(
        get_locks_text(locks),
        reply_markup=locks_keyboard(locks)
    )

    logger.info("Locks panel sent successfully")


# ==================================================
# /locks
# ==================================================

@router.message(Command("locks"))
async def locks_command(message: Message):
    logger.warning(
        "AZRAEL DEBUG: /locks RECEIVED | chat=%s | user=%s",
        message.chat.id,
        message.from_user.id if message.from_user else None
    )

    await show_locks_panel(message)


# ==================================================
# PERSIAN COMMAND
# ==================================================

@router.message(F.text.regexp(r"^(قفل‌ها|قفل ها|قفلها|قفل|پنل قفل‌ها|پنل قفل ها)$"))
async def locks_text_command(message: Message):
    logger.warning(
        "AZRAEL DEBUG: Persian locks command received | text=%r",
        message.text
    )

    await show_locks_panel(message)


# ==================================================
# PANEL CALLBACK
# ==================================================

@router.callback_query(F.data == "menu:locks")
async def open_locks_callback(callback: CallbackQuery):
    logger.info("menu:locks callback received")

    if not callback.message:
        await callback.answer()
        return

    chat = callback.message.chat

    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await callback.answer("این پنل فقط داخل گروه قابل استفاده است.", show_alert=True)
        return

    if not await is_group_admin(callback.bot, chat.id, callback.from_user.id):
        await callback.answer("⛔ فقط مدیران گروه اجازه دسترسی دارند.", show_alert=True)
        return

    await ensure_group(chat.id, chat.title or "")
    await update_panel(callback.message, chat.id)
    await callback.answer()


# ==================================================
# TOGGLE SINGLE LOCK
# ==================================================

@router.callback_query(F.data.startswith("lock:"))
async def toggle_lock(callback: CallbackQuery):
    logger.info("Lock toggle callback: %s", callback.data)

    if not callback.message:
        await callback.answer()
        return

    chat = callback.message.chat

    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await callback.answer("فقط داخل گروه قابل استفاده است.", show_alert=True)
        return

    if not await is_group_admin(callback.bot, chat.id, callback.from_user.id):
        await callback.answer("⛔ فقط مدیران اجازه تغییر قفل‌ها را دارند.", show_alert=True)
        return

    lock_type = callback.data.split(":", 1)[1]

    if lock_type not in LOCKS:
        await callback.answer("قفل نامعتبر است.", show_alert=True)
        return

    try:
        await ensure_group(chat.id, chat.title or "")
        current = await get_locks(chat.id)
        new_status = not current[lock_type]

        await set_lock(chat.id, lock_type, new_status)
        await update_panel(callback.message, chat.id)

        await callback.answer(
            f"{'🔒 قفل شد' if new_status else '🔓 باز شد'}: {LOCKS[lock_type]}"
        )

    except Exception:
        logger.exception("Toggle lock failed")
        await callback.answer("خطا در تغییر قفل.", show_alert=True)


# ==================================================
# OPEN ALL
# ==================================================

@router.callback_query(F.data == "locks:open_all")
async def open_all_locks(callback: CallbackQuery):
    logger.info("Open all locks callback")

    if not callback.message:
        await callback.answer()
        return

    chat = callback.message.chat

    if not await is_group_admin(callback.bot, chat.id, callback.from_user.id):
        await callback.answer("⛔ فقط مدیران اجازه دارند.", show_alert=True)
        return

    try:
        for key in LOCKS:
            await set_lock(chat.id, key, False)

        await update_panel(callback.message, chat.id)
        await callback.answer("🔓 تمام قفل‌ها باز شدند.")

    except Exception:
        logger.exception("Open all failed")
        await callback.answer("خطا در بازکردن قفل‌ها.", show_alert=True)


# ==================================================
# CLOSE ALL
# ==================================================

@router.callback_query(F.data == "locks:close_all")
async def close_all_locks(callback: CallbackQuery):
    logger.info("Close all locks callback")

    if not callback.message:
        await callback.answer()
        return

    chat = callback.message.chat

    if not await is_group_admin(callback.bot, chat.id, callback.from_user.id):
        await callback.answer("⛔ فقط مدیران اجازه دارند.", show_alert=True)
        return

    try:
        for key in LOCKS:
            await set_lock(chat.id, key, True)

        await update_panel(callback.message, chat.id)
        await callback.answer("🔒 تمام قفل‌ها فعال شدند.")

    except Exception:
        logger.exception("Close all failed")
        await callback.answer("خطا در فعال‌کردن قفل‌ها.", show_alert=True)
