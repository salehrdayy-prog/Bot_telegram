import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_group_settings
from utils import is_admin, LINK_REGEX

log = logging.getLogger(__name__)

async def filter_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    if not message or not user or chat.type not in ["group", "supergroup"]:
        return
    if await is_admin(update, context):
        return

    settings = get_group_settings(chat.id)
    should_delete = False
    reason = ""

    text_content = message.text or message.caption or ""
    username_regex = r"@[a-zA-Z0-9_]{5,}"

    if settings['lock_link'] and LINK_REGEX.search(text_content):
        should_delete, reason = True, "لینک"
    elif settings['lock_forward'] and (message.forward_from or message.forward_from_chat or message.forward_origin):
        should_delete, reason = True, "فوروارد"
    elif settings['lock_username'] and text_content and __import__('re').search(username_regex, text_content):
        should_delete, reason = True, "آیدی/یوزرنیم"
    elif settings['lock_hashtag'] and text_content and '#' in text_content:
        should_delete, reason = True, "هشتگ"
    elif settings['lock_sticker'] and message.sticker:
        should_delete, reason = True, "استیکر"
    elif settings['lock_gif'] and message.animation:
        should_delete, reason = True, "گیف"
    elif settings['lock_photo'] and message.photo:
        should_delete, reason = True, "عکس"
    elif settings['lock_video'] and message.video:
        should_delete, reason = True, "ویدیو"
    elif settings['lock_file'] and message.document:
        should_delete, reason = True, "فایل"
    elif settings['lock_voice'] and message.voice:
        should_delete, reason = True, "پیام صوتی"
    elif settings['lock_bots'] and user.is_bot:
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
