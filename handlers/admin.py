import logging
from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ChatPermissions
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

from config import MAX_WARNINGS, BOT_NAME

from database import (
    LOCKS,
    add_warning,
    get_warnings,
    reset_warnings,
    ensure_group,
    get_locks,
    set_lock,
)

from keyboards import locks_keyboard
from utils import is_admin, parse_duration, normalize_text


router = Router()
logger = logging.getLogger("AZRAEL.ADMIN")


COMMANDS = {
    "پینگ",
    "شناسه",
    "اطلاعات",
    "مدیران",
    "اخطار",
    "حذف_اخطار",
    "تعداد_اخطار",
    "سکوت",
    "لغو_سکوت",
    "مسدود",
    "رفع_مسدودی",
    "اخراج",
}


# ==================================================
# HELPERS
# ==================================================

def get_command(message: Message):
    text = message.text or ""
    parts = text.strip().split()

    if not parts:
        return None, []

    command = parts[0].split("@")[0].lower()

    if command.startswith("/"):
        command = command[1:]

    return normalize_text(command), parts[1:]


async def get_target(message: Message, args: list):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id, args

    if args:
        try:
            return int(args[0]), args[1:]
        except ValueError:
            pass

    return None, args


async def check_admin(message: Message):

    if message.chat.type not in (
        ChatType.GROUP,
        ChatType.SUPERGROUP
    ):
        await message.reply("❌ این دستور فقط در گروه قابل استفاده است.")
        return False

    if not message.from_user:
        return False

    if not await is_admin(
        message.bot,
        message.chat.id,
        message.from_user.id
    ):
        await message.reply("⛔ فقط مدیران گروه می‌توانند این دستور را اجرا کنند.")
        return False

    return True


async def check_bot_admin(message: Message):

    try:
        bot_info = await message.bot.get_me()

        member = await message.bot.get_chat_member(
            message.chat.id,
            bot_info.id
        )

        if member.status != "administrator":
            await message.reply("❌ ربات باید مدیر گروه باشد.")
            return False

        return True

    except Exception:
        logger.exception("Bot admin check failed")
        await message.reply("❌ امکان بررسی دسترسی ربات وجود ندارد.")
        return False


async def check_target(message: Message, user_id: int):

    try:
        member = await message.bot.get_chat_member(
            message.chat.id,
            user_id
        )

        if member.status in ("administrator", "creator"):
            await message.reply("❌ امکان اجرای این عملیات روی مدیران وجود ندارد.")
            return False

        return True

    except Exception:
        await message.reply("❌ کاربر موردنظر پیدا نشد.")
        return False


# ==================================================
# BASIC COMMANDS
# ==================================================

@router.message(Command("id"))
async def get_id(message: Message):

    if message.from_user:
        await message.reply(
            f"👤 شناسه کاربری: {message.from_user.id}\n"
            f"🏘 شناسه گروه: {message.chat.id}"
        )


@router.message(Command("ping"))
async def ping(message: Message):
    await message.reply("🏓 ربات فعال است!")


@router.message(Command("info"))
async def bot_info(message: Message):

    await message.reply(
        f"🤖 {BOT_NAME} | عزرائیل\n"
        "نسخه: 0.2.0\n"
        "وضعیت: فعال"
    )


@router.message(Command("admins"))
async def list_admins(message: Message):

    if message.chat.type not in (
        ChatType.GROUP,
        ChatType.SUPERGROUP
    ):
        return

    try:
        admins = await message.bot.get_chat_administrators(
            message.chat.id
        )

        lines = ["👮 مدیران گروه:\n"]

        for admin in admins:
            user = admin.user
            username = f" (@{user.username})" if user.username else ""

            lines.append(f"• {user.full_name}{username}")

        await message.reply("\n".join(lines))

    except Exception:
        logger.exception("Failed to get administrators")
        await message.reply("❌ دریافت فهرست مدیران ناموفق بود.")


# ==================================================
# LOCK PANEL
# ==================================================

def get_locks_text(locks: dict):

    active = sum(1 for value in locks.values() if value)
    total = len(LOCKS)
    opened = total - active

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "🔒 <b>پنل مدیریت قفل‌های AZRAEL</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🔴 قفل‌های فعال: {active}\n"
        f"🟢 قفل‌های باز: {opened}\n"
        f"📊 مجموع قفل‌ها: {total}\n\n"
        "برای تغییر وضعیت هر قفل، روی دکمه آن بزن.\n"
        "━━━━━━━━━━━━━━━━━━"
    )


async def show_locks_panel(message: Message):

    if message.chat.type not in (
        ChatType.GROUP,
        ChatType.SUPERGROUP
    ):
        await message.reply("❌ این پنل فقط داخل گروه قابل استفاده است.")
        return

    if not message.from_user:
        return

    if not await is_admin(
        message.bot,
        message.chat.id,
        message.from_user.id
    ):
        await message.reply("⛔ فقط مدیران گروه می‌توانند پنل قفل‌ها را باز کنند.")
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


async def update_locks_panel(message: Message):

    locks = await get_locks(message.chat.id)

    try:
        await message.edit_text(
            get_locks_text(locks),
            reply_markup=locks_keyboard(locks)
        )

    except TelegramBadRequest as error:
        if "message is not modified" not in str(error).lower():
            raise


@router.message(Command("locks"))
async def locks_command(message: Message):

    logger.info(
        "/locks received | chat=%s | user=%s",
        message.chat.id,
        message.from_user.id if message.from_user else None
    )

    await show_locks_panel(message)


@router.message(
    F.text.regexp(
        r"^(قفل‌ها|قفل ها|قفلها|قفل|پنل قفل‌ها|پنل قفل ها)$"
    )
)
async def locks_text_command(message: Message):
    await show_locks_panel(message)


# ==================================================
# LOCK CALLBACKS
# ==================================================

async def check_callback_admin(callback: CallbackQuery):

    if not callback.message:
        await callback.answer("❌ پیام معتبر نیست.", show_alert=True)
        return False

    if callback.message.chat.type not in (
        ChatType.GROUP,
        ChatType.SUPERGROUP
    ):
        await callback.answer("❌ فقط داخل گروه قابل استفاده است.", show_alert=True)
        return False

    if not callback.from_user:
        return False

    if not await is_admin(
        callback.bot,
        callback.message.chat.id,
        callback.from_user.id
    ):
        await callback.answer("⛔ فقط مدیران گروه دسترسی دارند.", show_alert=True)
        return False

    return True


@router.callback_query(F.data == "menu:locks")
async def locks_menu_callback(callback: CallbackQuery):

    if not await check_callback_admin(callback):
        return

    message = callback.message

    await ensure_group(
        message.chat.id,
        message.chat.title or ""
    )

    await update_locks_panel(message)
    await callback.answer()


@router.callback_query(F.data.startswith("lock:"))
async def toggle_lock_callback(callback: CallbackQuery):

    if not await check_callback_admin(callback):
        return

    message = callback.message
    lock_type = callback.data.split(":", 1)[1]

    if lock_type not in LOCKS:
        await callback.answer("❌ نوع قفل نامعتبر است.", show_alert=True)
        return

    group_id = message.chat.id

    await ensure_group(
        group_id,
        message.chat.title or ""
    )

    locks = await get_locks(group_id)

    new_status = not locks.get(lock_type, False)

    await set_lock(
        group_id,
        lock_type,
        new_status
    )

    await update_locks_panel(message)

    await callback.answer(
        "🔒 قفل فعال شد." if new_status else "🔓 قفل باز شد."
    )


@router.callback_query(F.data == "locks:open_all")
async def open_all_locks(callback: CallbackQuery):

    if not await check_callback_admin(callback):
        return

    message = callback.message
    group_id = message.chat.id

    await ensure_group(
        group_id,
        message.chat.title or ""
    )

    for lock_type in LOCKS:
        await set_lock(group_id, lock_type, False)

    await update_locks_panel(message)
    await callback.answer("🔓 تمام قفل‌ها باز شدند.")


@router.callback_query(F.data == "locks:close_all")
async def close_all_locks(callback: CallbackQuery):

    if not await check_callback_admin(callback):
        return

    message = callback.message
    group_id = message.chat.id

    await ensure_group(
        group_id,
        message.chat.title or ""
    )

    for lock_type in LOCKS:
        await set_lock(group_id, lock_type, True)

    await update_locks_panel(message)
    await callback.answer("🔒 تمام قفل‌ها بسته شدند.")


# ==================================================
# PERSIAN MANAGEMENT COMMANDS
# ==================================================

@router.message(
    F.text.regexp(
        r"^(?:پینگ|شناسه|اطلاعات|مدیران|اخطار|حذف_اخطار|تعداد_اخطار|سکوت|لغو_سکوت|مسدود|رفع_مسدودی|اخراج)(?:\s|$)"
    )
)
async def management_commands(message: Message):

    command, args = get_command(message)

    if command not in COMMANDS:
        return

    if not await check_admin(message):
        return

    if command == "پینگ":
        await message.reply("🏓 ربات فعال است!")
        return

    if command == "شناسه":

        target_id = (
            message.reply_to_message.from_user.id
            if message.reply_to_message
            and message.reply_to_message.from_user
            else message.from_user.id
        )

        await message.reply(
            f"👤 شناسه کاربر: {target_id}\n"
            f"🏘 شناسه گروه: {message.chat.id}"
        )
        return

    if command == "اطلاعات":

        await message.reply(
            f"🤖 {BOT_NAME} | عزرائیل\n"
            "نسخه: 0.2.0\n"
            f"شناسه گروه: {message.chat.id}\n"
            "وضعیت: فعال"
        )
        return

    if command == "مدیران":
        await list_admins(message)
        return

    if command == "تعداد_اخطار":

        target_id, _ = await get_target(message, args)

        if target_id is None:
            await message.reply("❌ روی پیام کاربر ریپلای کن یا شناسه او را وارد کن.")
            return

        count = await get_warnings(
            message.chat.id,
            target_id
        )

        await message.reply(
            f"⚠️ تعداد اخطارها: {count}/{MAX_WARNINGS}"
        )
        return

    if command in (
        "اخطار",
        "حذف_اخطار",
        "سکوت",
        "لغو_سکوت",
        "مسدود",
        "رفع_مسدودی",
        "اخراج"
    ):

        target_id, remaining = await get_target(message, args)

        if target_id is None:
            await message.reply("❌ روی پیام کاربر ریپلای کن یا شناسه او را وارد کن.")
            return

        if target_id == message.from_user.id:
            await message.reply("❌ نمی‌توانی این عملیات را روی خودت انجام دهی.")
            return

        if not await check_bot_admin(message):
            return

        if command != "رفع_مسدودی":
            if not await check_target(message, target_id):
                return

        reason = " ".join(remaining).strip()

        # WARN
        if command == "اخطار":

            await add_warning(
                message.chat.id,
                target_id,
                reason
            )

            count = await get_warnings(
                message.chat.id,
                target_id
            )

            if count >= MAX_WARNINGS:

                try:
                    await message.bot.restrict_chat_member(
                        chat_id=message.chat.id,
                        user_id=target_id,
                        permissions=ChatPermissions(
                            can_send_messages=False
                        ),
                        until_date=(
                            datetime.now(timezone.utc)
                            + timedelta(hours=1)
                        )
                    )

                    await reset_warnings(
                        message.chat.id,
                        target_id
                    )

                    await message.reply(
                        f"⛔ کاربر {target_id} به سقف اخطار رسید.\n"
                        "🔇 سکوت خودکار به مدت یک ساعت اعمال شد."
                    )

                except Exception:
                    logger.exception("Automatic mute failed")
                    await message.reply(
                        f"⚠️ اخطار ثبت شد ({count}/{MAX_WARNINGS})، "
                        "اما سکوت خودکار ناموفق بود."
                    )

            else:

                await message.reply(
                    "⚠️ یک اخطار ثبت شد.\n"
                    f"👤 کاربر: {target_id}\n"
                    f"📊 اخطارها: {count}/{MAX_WARNINGS}\n"
                    f"📝 دلیل: {reason or 'بدون دلیل'}"
                )

        # RESET WARNINGS
        elif command == "حذف_اخطار":

            await reset_warnings(
                message.chat.id,
                target_id
            )

            await message.reply(
                f"✅ تمام اخطارهای کاربر {target_id} پاک شدند."
            )

        # MUTE
        elif command == "سکوت":

            duration = (
                parse_duration(remaining[0])
                if remaining else None
            )

            if remaining and duration is None:
                await message.reply(
                    "❌ زمان نامعتبر است.\n"
                    "نمونه: سکوت 30m یا سکوت 2h"
                )
                return

            until_date = (
                datetime.now(timezone.utc)
                + timedelta(seconds=duration)
                if duration else None
            )

            try:
                await message.bot.restrict_chat_member(
                    chat_id=message.chat.id,
                    user_id=target_id,
                    permissions=ChatPermissions(
                        can_send_messages=False
                    ),
                    until_date=until_date
                )

                await message.reply(
                    f"🔇 کاربر {target_id} سکوت شد.\n"
                    f"⏱ مدت: {'دائمی' if not duration else remaining[0]}"
                )

            except Exception:
                logger.exception("Mute failed")
                await message.reply("❌ اجرای سکوت ناموفق بود.")

        # UNMUTE
        elif command == "لغو_سکوت":

            try:
                await message.bot.restrict_chat_member(
                    chat_id=message.chat.id,
                    user_id=target_id,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_audios=True,
                        can_send_documents=True,
                        can_send_photos=True,
                        can_send_videos=True,
                        can_send_video_notes=True,
                        can_send_voice_notes=True,
                        can_send_polls=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True
                    )
                )

                await message.reply(
                    f"🔊 سکوت کاربر {target_id} برداشته شد."
                )

            except Exception:
                logger.exception("Unmute failed")
                await message.reply("❌ لغو سکوت ناموفق بود.")

        # BAN
        elif command == "مسدود":

            try:
                await message.bot.ban_chat_member(
                    chat_id=message.chat.id,
                    user_id=target_id
                )

                await message.reply(
                    f"⛔ کاربر {target_id} از گروه مسدود شد."
                )

            except Exception:
                logger.exception("Ban failed")
                await message.reply("❌ مسدودسازی ناموفق بود.")

        # UNBAN
        elif command == "رفع_مسدودی":

            try:
                await message.bot.unban_chat_member(
                    chat_id=message.chat.id,
                    user_id=target_id,
                    only_if_banned=True
                )

                await message.reply(
                    f"✅ مسدودیت کاربر {target_id} برداشته شد."
                )

            except Exception:
                logger.exception("Unban failed")
                await message.reply("❌ رفع مسدودیت ناموفق بود.")

        # KICK
        elif command == "اخراج":

            try:
                await message.bot.ban_chat_member(
                    chat_id=message.chat.id,
                    user_id=target_id
                )

                await message.bot.unban_chat_member(
                    chat_id=message.chat.id,
                    user_id=target_id
                )

                await message.reply(
                    f"👢 کاربر {target_id} از گروه اخراج شد."
                )

            except Exception:
                logger.exception("Kick failed")
                await message.reply("❌ اخراج کاربر ناموفق بود.")
