import logging
from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import ChatPermissions

from config import MAX_WARNINGS
from database import (
add_warning,
get_warnings,
reset_warnings,
)
from utils import is_admin, parse_duration, normalize_text

router = Router()
logger = logging.getLogger(name)

COMMANDS = {
"پینگ", "شناسه", "اطلاعات", "مدیران",
"اخطار", "حذف_اخطار", "تعداد_اخطار",
"سکوت", "لغو_سکوت",
"مسدود", "رفع_مسدودی", "اخراج",
}

def get_command(message: Message):
text = message.text or ""
parts = text.strip().split()

if not parts:
    return None, []

command = parts[0].split("@")[0].lower()

if command.startswith("/"):
    command = command[1:]

command = normalize_text(command)

return command, parts[1:]

async def get_target(message: Message, args: list):
if message.reply_to_message and message.reply_to_message.from_user:
return message.reply_to_message.from_user.id, args

if args:
    try:
        user_id = int(args[0])
        return user_id, args[1:]
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
"🤖 ربات مدیریت گروه\n"
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

        lines.append(
            f"• {user.full_name}{username}"
        )

    await message.reply("\n".join(lines))

except Exception:
    logger.exception("Failed to get administrators")
    await message.reply("❌ دریافت فهرست مدیران ناموفق بود.")

@router.message(F.text)
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
        f"👤 شناسه کاربر: `{target_id}`\n"
        f"🏘 شناسه گروه: `{message.chat.id}`",
        parse_mode="Markdown"
    )
    return

if command == "اطلاعات":
    await message.reply(
        f"🤖 Unlimited Bot\n"
        f"نسخه: 0.2.0\n"
        f"شناسه گروه: {message.chat.id}\n"
        f"وضعیت: فعال"
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

    count = await get_warnings(message.chat.id, target_id)

    await message.reply(
        f"⚠️ تعداد اخطارهای کاربر: {count}/{MAX_WARNINGS}"
    )
    return

if command in ("اخطار", "حذف_اخطار", "سکوت",
               "لغو_سکوت", "مسدود", "رفع_مسدودی", "اخراج"):

    target_id, remaining = await get_target(message, args)

    if target_id is None:
        await message.reply(
            "❌ روی پیام کاربر ریپلای کن یا شناسه او را وارد کن."
        )
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
                    until_date=datetime.now(timezone.utc)
                    + timedelta(hours=1)
                )

                await reset_warnings(
                    message.chat.id,
                    target_id
                )

                await message.reply(
                    f"⛔ کاربر {target_id} به سقف اخطار رسید.\n"
                    f"🔇 سکوت خودکار به مدت یک ساعت اعمال شد."
                )

            except Exception:
                logger.exception("Automatic mute failed")
                await message.reply(
                    f"⚠️ اخطار ثبت شد ({count}/{MAX_WARNINGS})، "
                    "اما سکوت خودکار ناموفق بود."
                )

        else:
            await message.reply(
                f"⚠️ یک اخطار ثبت شد.\n"
                f"👤 کاربر: {target_id}\n"
                f"📊 اخطارها: {count}/{MAX_WARNINGS}\n"
                f"📝 دلیل: {reason or 'بدون دلیل'}"
            )

    elif command == "حذف_اخطار":
        await reset_warnings(message.chat.id, target_id)

        await message.reply(
            f"✅ تمام اخطارهای کاربر {target_id} پاک شدند."
        )

    elif command == "سکوت":
        duration = parse_duration(remaining[0]) if remaining else None

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
