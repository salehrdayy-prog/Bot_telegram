from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from utils import is_admin

router = Router()


@router.message(Command("id"))
async def get_id(message: Message):
    if message.from_user:
        await message.reply(
            f"👤 شناسه کاربری: `{message.from_user.id}`\n"
            f"🏘 شناسه گروه: `{message.chat.id}`",
            parse_mode="Markdown"
        )


@router.message(Command("admins"))
async def list_admins(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    try:
        admins = await message.bot.get_chat_administrators(message.chat.id)

        text = "👮 مدیران گروه:\n\n"

        for admin in admins:
            user = admin.user

            name = user.full_name
            username = f" (@{user.username})" if user.username else ""

            text += f"• {name}{username}\n"

        await message.reply(text)

    except Exception:
        await message.reply("❌ دریافت فهرست مدیران ناموفق بود.")


@router.message(Command("ping"))
async def ping(message: Message):
    await message.reply("🏓 ربات فعال است!")


@router.message(Command("info"))
async def bot_info(message: Message):
    await message.reply(
        "🤖 ربات مدیریت گروه\n"
        "نسخه: 0.1.0\n"
        "وضعیت: فعال"
    )
