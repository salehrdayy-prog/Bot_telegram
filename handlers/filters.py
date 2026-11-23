import time
from collections import defaultdict, deque

from aiogram import Router
from aiogram.types import Message
from aiogram.enums import ChatType

from config import FLOOD_LIMIT, FLOOD_TIME
from database import get_lock
from utils import contains_link, normalize_text

router = Router()

# حافظه ضدفلود
_user_messages = defaultdict(deque)

# فیلتر کلمات هر گروه
_group_bad_words = defaultdict(set)


def register_bad_words(group_id: int, words: list[str]):
    _group_bad_words[group_id] = {
        normalize_text(word) for word in words if word.strip()
    }


def is_flood(group_id: int, user_id: int) -> bool:
    now = time.monotonic()
    key = (group_id, user_id)
    messages = _user_messages[key]

    while messages and now - messages[0] > FLOOD_TIME:
        messages.popleft()

    messages.append(now)

    return len(messages) > FLOOD_LIMIT


def contains_bad_word(group_id: int, text: str) -> bool:
    normalized = normalize_text(text)

    return any(
        word and word in normalized
        for word in _group_bad_words[group_id]
    )


@router.message()
async def filter_messages(message: Message):
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    if not message.from_user or message.from_user.is_bot:
        return

    group_id = message.chat.id
    user_id = message.from_user.id
    text = message.text or message.caption or ""

    # بررسی مدیر گروه
    try:
        member = await message.bot.get_chat_member(group_id, user_id)

        if member.status in ("administrator", "creator"):
            return
    except Exception:
        pass

    # ضدفلود
    if is_flood(group_id, user_id):
        try:
            await message.delete()
        except Exception:
            pass
        return

    # قفل لینک
    if text and await get_lock(group_id, "links") and contains_link(text):
        try:
            await message.delete()
        except Exception:
            pass
        return

    # قفل عکس
    if message.photo and await get_lock(group_id, "photos"):
        await message.delete()
        return

    # قفل ویدیو
    if message.video and await get_lock(group_id, "videos"):
        await message.delete()
        return

    # قفل استیکر
    if message.sticker and await get_lock(group_id, "stickers"):
        await message.delete()
        return

    # قفل ویس
    if message.voice and await get_lock(group_id, "voice"):
        await message.delete()
        return

    # قفل فایل
    if message.document and await get_lock(group_id, "files"):
        await message.delete()
        return

    # قفل گیف
    if message.animation and await get_lock(group_id, "gifs"):
        await message.delete()
        return

    # قفل موسیقی
    if message.audio and await get_lock(group_id, "audio"):
        await message.delete()
        return

    # فیلتر کلمات
    if text and contains_bad_word(group_id, text):
        try:
            await message.delete()
        except Exception:
            pass
