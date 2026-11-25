import time
import unicodedata

from collections import defaultdict, deque

from aiogram import Router
from aiogram.types import Message
from aiogram.enums import ChatType

from config import FLOOD_LIMIT, FLOOD_TIME

from database import get_lock

from utils import contains_link, normalize_text


router = Router()


# ==================================================
# MEMORY
# ==================================================

_user_messages = defaultdict(deque)
_group_bad_words = defaultdict(set)


# ==================================================
# BAD WORDS
# ==================================================

def register_bad_words(group_id: int, words: list[str]):

    _group_bad_words[group_id] = {
        normalize_text(word)
        for word in words
        if word.strip()
    }


def contains_bad_word(group_id: int, text: str) -> bool:

    normalized = normalize_text(text)

    return any(
        word and word in normalized
        for word in _group_bad_words[group_id]
    )


# ==================================================
# ANTI FLOOD
# ==================================================

def is_flood(group_id: int, user_id: int) -> bool:

    now = time.monotonic()

    key = (group_id, user_id)

    messages = _user_messages[key]

    while messages and now - messages[0] > FLOOD_TIME:
        messages.popleft()

    messages.append(now)

    return len(messages) > FLOOD_LIMIT


# ==================================================
# SAFE DELETE
# ==================================================

async def safe_delete(message: Message):

    try:
        await message.delete()
        return True

    except Exception:
        return False


# ==================================================
# ENTITY CHECK
# ==================================================

def has_entity(message: Message, entity_type: str) -> bool:

    entities = (
        (message.entities or [])
        + (message.caption_entities or [])
    )

    return any(
        getattr(entity.type, "value", entity.type) == entity_type
        for entity in entities
    )


# ==================================================
# EMOJI CHECK
# ==================================================

def contains_emoji(text: str) -> bool:

    for char in text:

        code = ord(char)

        if (
            0x1F000 <= code <= 0x1FAFF
            or 0x2600 <= code <= 0x27BF
            or unicodedata.category(char) == "So"
        ):
            return True

    return False


# ==================================================
# FORWARD CHECK
# ==================================================

def is_forwarded(message: Message) -> bool:
    return message.forward_origin is not None


# ==================================================
# SERVICE MESSAGE CHECK
# ==================================================

def is_service_message(message: Message) -> bool:

    service_fields = (
        "new_chat_members",
        "left_chat_member",
        "new_chat_title",
        "new_chat_photo",
        "delete_chat_photo",
        "pinned_message",
        "group_chat_created",
        "supergroup_chat_created",
        "channel_chat_created",
        "migrate_to_chat_id",
        "migrate_from_chat_id",
        "forum_topic_created",
        "forum_topic_closed",
        "forum_topic_reopened",
        "forum_topic_edited",
        "general_forum_topic_hidden",
        "general_forum_topic_unhidden",
        "video_chat_scheduled",
        "video_chat_started",
        "video_chat_ended",
        "video_chat_participants_invited",
        "write_access_allowed",
        "proximity_alert_triggered",
        "boost_added",
    )

    return any(
        getattr(message, field, None)
        for field in service_fields
    )


# ==================================================
# LOCK CHECK
# ==================================================

async def check_lock(group_id: int, lock_type: str) -> bool:

    try:
        return await get_lock(group_id, lock_type)

    except Exception:
        return False


# ==================================================
# ADMIN CHECK
# ==================================================

async def is_group_admin(message: Message) -> bool:

    if not message.from_user:
        return False

    try:

        member = await message.bot.get_chat_member(
            message.chat.id,
            message.from_user.id
        )

        return member.status in (
            "administrator",
            "creator"
        )

    except Exception:
        return False


# ==================================================
# MAIN FILTER
# ==================================================

@router.message()
async def filter_messages(message: Message):

    if message.chat.type not in (
        ChatType.GROUP,
        ChatType.SUPERGROUP
    ):
        return

    group_id = message.chat.id

    # ==================================================
    # SERVICE MESSAGES
    # ==================================================

    if is_service_message(message):

        if await check_lock(group_id, "service_messages"):
            await safe_delete(message)
            return

        if (
            message.new_chat_members
            and await check_lock(group_id, "new_members")
        ):
            await safe_delete(message)
            return

        if (
            message.new_chat_title
            and await check_lock(group_id, "group_info")
        ):
            await safe_delete(message)
            return

        if (
            (
                message.new_chat_photo
                or message.delete_chat_photo
            )
            and await check_lock(group_id, "group_photo")
        ):
            await safe_delete(message)
            return

        return

    # ==================================================
    # USER CHECK
    # ==================================================

    if not message.from_user:
        return

    user_id = message.from_user.id

    # پیام خود ربات فیلتر نشود.
    if user_id == message.bot.id:
        return

    # ==================================================
    # BOT MESSAGE LOCK
    # ==================================================

    if message.from_user.is_bot:

        if await check_lock(group_id, "bots"):
            await safe_delete(message)

        return

    # ==================================================
    # ADMIN CHECK
    # ==================================================

    if await is_group_admin(message):
        return

    # ==================================================
    # MESSAGE CONTENT
    # ==================================================

    text = message.text or message.caption or ""

    # ==================================================
    # ANTI FLOOD
    # ==================================================

    if is_flood(group_id, user_id):
        await safe_delete(message)
        return

    # ==================================================
    # LINKS
    # ==================================================

    if (
        text
        and await check_lock(group_id, "links")
        and contains_link(text)
    ):
        await safe_delete(message)
        return

    # ==================================================
    # FORWARDED MESSAGES
    # ==================================================

    if (
        is_forwarded(message)
        and await check_lock(group_id, "forwards")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # TEXT MESSAGES
    # ==================================================

    if (
        message.text
        and await check_lock(group_id, "text")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # HASHTAGS
    # ==================================================

    if (
        has_entity(message, "hashtag")
        and await check_lock(group_id, "hashtags")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # MENTIONS
    # ==================================================

    if (
        (
            has_entity(message, "mention")
            or has_entity(message, "text_mention")
        )
        and await check_lock(group_id, "mentions")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # PHONE NUMBERS
    # ==================================================

    if (
        has_entity(message, "phone_number")
        and await check_lock(group_id, "phone_numbers")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # EMOJIS
    # ==================================================

    if (
        text
        and contains_emoji(text)
        and await check_lock(group_id, "emojis")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # PHOTOS
    # ==================================================

    if (
        message.photo
        and await check_lock(group_id, "photos")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # VIDEOS
    # ==================================================

    if (
        message.video
        and await check_lock(group_id, "videos")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # GIFS
    # ==================================================

    if (
        message.animation
        and await check_lock(group_id, "gifs")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # STICKERS
    # ==================================================

    if (
        message.sticker
        and await check_lock(group_id, "stickers")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # VOICE
    # ==================================================

    if (
        message.voice
        and await check_lock(group_id, "voice")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # VIDEO NOTES
    # ==================================================

    if (
        message.video_note
        and await check_lock(group_id, "video_notes")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # AUDIO
    # ==================================================

    if (
        message.audio
        and await check_lock(group_id, "audio")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # FILES
    # ==================================================

    if (
        message.document
        and await check_lock(group_id, "files")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # CONTACTS
    # ==================================================

    if (
        message.contact
        and await check_lock(group_id, "contacts")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # LOCATIONS
    # ==================================================

    if (
        (
            message.location
            or message.venue
        )
        and await check_lock(group_id, "locations")
    ):
        await safe_delete(message)
        return

    # ==================================================
    # POLLS
    # ==================================================

    if message.poll:

        if (
            await check_lock(group_id, "polls")
            or await check_lock(group_id, "poll_creation")
        ):
            await safe_delete(message)
            return

    # ==================================================
    # BAD WORDS
    # ==================================================

    if text and contains_bad_word(group_id, text):
        await safe_delete(message)
        return
