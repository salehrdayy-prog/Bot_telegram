from telegram import ChatMember, Chat
from telegram.error import TelegramError

async def is_admin(update, context):
    """بررسی اینکه آیا فرستنده پیام ادمین است (شامل مالک)"""
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == Chat.PRIVATE:
        return True
    try:
        member = await chat.get_member(user.id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except TelegramError:
        return False

async def get_target_user(update, context):
    """دریافت کاربر هدف: اگر ریپلای باشد، کاربر ریپلای شده، در غیر این صورت فرستنده"""
    message = update.effective_message
    if message.reply_to_message:
        return message.reply_to_message.from_user
    return None
