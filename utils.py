import re
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.types import ChatMember


def normalize_text(text: str) -> str:
    """یکسان‌سازی حروف فارسی و عربی"""
    if not text:
        return ""

    return (
        text.replace("ي", "ی")
        .replace("ك", "ک")
        .replace("ة", "ه")
        .replace("\u200c", " ")
        .strip()
    )


def contains_link(text: str) -> bool:
    """تشخیص لینک و آدرس‌های اینترنتی"""
    if not text:
        return False

    patterns = [
        r"https?://",
        r"www\.",
        r"t\.me/",
        r"telegram\.me/",
        r"\.com\b",
        r"\.ir\b",
        r"\.net\b",
        r"\.org\b",
    ]

    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in patterns
    )


def format_user_name(first_name: str, username: str = "") -> str:
    """ساخت نام نمایشی کاربر"""
    if username:
        return f"{first_name} (@{username})"

    return first_name or "کاربر"


def format_duration(seconds: int) -> str:
    """تبدیل ثانیه به متن قابل نمایش"""
    seconds = max(0, int(seconds))

    if seconds < 60:
        return f"{seconds} ثانیه"

    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} دقیقه"

    if seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        if minutes:
            return f"{hours} ساعت و {minutes} دقیقه"

        return f"{hours} ساعت"

    days = seconds // 86400
    hours = (seconds % 86400) // 3600

    if hours:
        return f"{days} روز و {hours} ساعت"

    return f"{days} روز"


def parse_duration(value: str):
    """خواندن زمان مثل 30s، 10m، 2h، 1d"""
    if not value:
        return None

    value = value.strip().lower()

    match = re.fullmatch(r"(\d+)\s*(s|m|h|d)", value)

    if not match:
        return None

    number = int(match.group(1))
    unit = match.group(2)

    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
    }

    seconds = number * multipliers[unit]

    if seconds <= 0:
        return None

    return seconds


def get_expiration(seconds: int):
    """محاسبه زمان پایان محدودیت"""
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


async def is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    """بررسی مدیر بودن کاربر"""
    try:
        member: ChatMember = await bot.get_chat_member(
            chat_id,
            user_id
        )

        return member.status in ("administrator", "creator")

    except Exception:
        return False


async def is_bot_admin(bot: Bot, chat_id: int) -> bool:
    """بررسی مدیر بودن خود ربات"""
    try:
        bot_info = await bot.get_me()

        member = await bot.get_chat_member(
            chat_id,
            bot_info.id
        )

        return member.status in ("administrator", "creator")

    except Exception:
        return False


def extract_command_args(text: str):
    """استخراج دستور و پارامترهای آن"""
    if not text:
        return None, []

    parts = text.strip().split()

    if not parts:
        return None, []

    command = parts[0].split("@")[0].lower()

    return command, parts[1:]


def safe_int(value, default=0):
    """تبدیل امن به عدد"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clean_text(text: str, max_length: int = 4000) -> str:
    """پاک‌سازی متن ورودی"""
    if not text:
        return ""

    text = text.strip()

    if len(text) > max_length:
        text = text[:max_length]

    return text
