import re
from telegram import Update
from telegram.ext import ContextTypes
from database import get_group_settings

LINK_REGEX = re.compile(r'(https?://|t\.me/|www\.)')

async def filter_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    if not message or not user or chat.type not in ["group", "supergroup"]:
        return
    
    # ادمین‌ها از فیلتر معاف هستند
    from utils import is_admin
    if await is_admin(update, context):
        return

    settings = get_group_settings(chat.id)
    should_delete = False
    reason = ""

    # بررسی لینک
    if settings['lock_link'] and message.text and LINK_REGEX.search(message.text):
        should_delete = True
        reason = "لینک"

    # بررسی فوروارد
    elif settings['lock_forward'] and (message.forward_from or message.forward_from_chat or message.forward_origin):
        should_delete = True
        reason = "فوروارد"

    # بررسی استیکر
    elif settings['lock_sticker'] and message.sticker:
        should_delete = True
        reason = "استیکر"

    # بررسی گیف
    elif settings['lock_gif'] and message.animation:
        should_delete = True
        reason = "گیف"

    # بررسی عکس
    elif settings['lock_photo'] and message.photo:
        should_delete = True
        reason = "عکس"

    # بررسی ویدیو
    elif settings['lock_video'] and message.video:
        should_delete = True
        reason = "ویدیو"

    # بررسی فایل
    elif settings['lock_file'] and message.document:
        should_delete = True
        reason = "فایل"

    # بررسی ویس
    elif settings['lock_voice'] and message.voice:
        should_delete = True
        reason = "پیام صوتی"

    if should_delete:
        try:
            await message.delete()
            warning = await context.bot.send_message(
                chat.id,
                f"⚠️ {user.mention_html()} ارسال {reason} در این گروه ممنوع است.",
                parse_mode="HTML"
            )
            # حذف پیام هشدار پس از ۵ ثانیه (نیاز به JobQueue)
            context.job_queue.run_once(
                lambda ctx: ctx.bot.delete_message(chat.id, warning.message_id),
                5,
                name=f"del_{warning.message_id}"
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Filter error: {e}")
