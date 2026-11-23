from aiogram import Router
from aiogram.types import Message
from aiogram.enums import ChatType

from database import ensure_group, get_group

router = Router()


DEFAULT_WELCOME = (
    "👋 سلام {name}!\n"
    "به گروه {group} خوش اومدی.\n"
    "امیدواریم لحظات خوبی داشته باشی ❤️"
)

DEFAULT_GOODBYE = (
    "👋 {name} از گروه خارج شد."
)


@router.message(lambda message: message.new_chat_members is not None)
async def welcome_new_members(message: Message):
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    await ensure_group(
        message.chat.id,
        message.chat.title or ""
    )

    group_data = await get_group(message.chat.id)

    if group_data and not group_data.get("welcome_enabled", 1):
        return

    for member in message.new_chat_members:
        if member.is_bot:
            continue

        name = member.first_name or "دوست عزیز"

        welcome_text = (
            group_data.get("welcome_text", DEFAULT_WELCOME)
            if group_data
            else DEFAULT_WELCOME
        )

        try:
            text = welcome_text.format(
                name=name,
                group=message.chat.title or "گروه"
            )
        except (KeyError, ValueError):
            text = DEFAULT_WELCOME.format(
                name=name,
                group=message.chat.title or "گروه"
            )

        await message.answer(text)


@router.message(lambda message: message.left_chat_member is not None)
async def goodbye_member(message: Message):
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    member = message.left_chat_member

    if member.is_bot:
        return

    name = member.first_name or "کاربر"

    await message.answer(
        DEFAULT_GOODBYE.format(name=name)
    )
