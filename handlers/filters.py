import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
from database import get_group_settings

log = logging.getLogger(__name__)

# الگوهای تشخیص
LINK_REGEX = re.compile(r'(https?://|t\.me/|www\.)')
USERNAME_REGEX = re.compile(r"@[a-zA-Z0-9_]{5,}")
HASHTAG_REGEX = re.compile(r"#\w+")
EMOJI_REGEX = re.compile(
    "[" 
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
    "\U0001F680-\U0001F6FF"  # Transport and Map
    "\U0001F1E0-\U0001F1FF"  # Flags
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251" 
    "]+", flags=re.UNICODE
)

async def filter_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    # فقط در گروه‌ها
    if not message or not user or chat.type not in ["group", "supergroup"]:
        return
    
    # اگر کاربر ادمین است، فیلترها روی او اعمال نمی‌شوند
    try:
        member = await chat.get_member(user.id)
        if member.status in ["administrator", "creator"]:
            return
    except Exception:
        pass # اگر خطایی رخ داد، ادامه بده

    settings = get_group_settings(chat.id)
    if not settings:
        return

    text_content = message.text or message.caption or ""
    should_delete = False
    reason = ""

    # بررسی قفل‌ها (دقیق‌تر)
    if settings.get('lock_link') and LINK_REGEX.search(text_content):
        should_delete, reason = True, "لینک"
    elif settings.get('lock_forward') and (message.forward_from or message.forward_from_chat or message.forward_origin):
        should_delete, reason = True, "فوروارد"
    elif settings.get('lock_username') and USERNAME_REGEX.search(text_content):
        should_delete, reason = True, "یوزرنیم"
    elif settings.get('lock_hashtag') and HASHTAG_REGEX.search(text_content):
        should_delete, reason = True, "هشتگ"
    elif settings.get('lock_emoji') and EMOJI_REGEX.search(text_content):
        should_delete, reason = True, "ایموجی"
    elif settings.get('lock_sticker') and message.sticker:
        should_delete, reason = True, "استیکر"
    elif settings.get('lock_gif') and message.animation:
        should_delete, reason = True, "گیف"
    elif settings.get('lock_photo') and message.photo:
        should_delete, reason = True, "عکس"
    elif settings.get('lock_video') and message.video:
        should_delete, reason = True, "ویدیو"
    elif settings.get('lock_file') and message.document:
        should_delete, reason = True, "فایل"
    elif settings.get('lock_voice') and message.voice:
        should_delete, reason = True, "پیام صوتی"
    elif settings.get('lock_audio') and message.audio:
        should_delete, reason = True, "صدا"
    elif settings.get('lock_poll') and message.poll:
        should_delete, reason = True, "نظرسنجی"
    elif settings.get('lock_contact') and message.contact:
        should_delete, reason = True, "مخاطب"
    elif settings.get('lock_location') and message.location:
        should_delete, reason = True, "موقعیت"
    elif settings.get('lock_game') and message.game:
        should_delete, reason = True, "بازی"
    elif settings.get('lock_bots') and user.is_bot:
        should_delete, reason = True, "ربات"

    if should_delete:
        try:
            await message.delete()
            warning = await context.bot.send_message(
                chat.id,
                f"⚠️ {user.mention_html()} ارسال {reason} ممنوع است.",
                parse_mode="HTML"
            )
            context.job_queue.run_once(
                lambda ctx: ctx.bot.delete_message(chat.id, warning.message_id),
                5, name=f"del_{warning.message_id}"
            )
        except Exception as e:
            log.error(f"Filter error: {e}")
