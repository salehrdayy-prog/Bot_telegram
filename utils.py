import re
from telegram import ChatMember, Chat
from telegram.error import TelegramError

LINK_REGEX = re.compile(r'(https?://|t\.me/|www\.)')

async def is_admin(update, context):
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
    message = update.effective_message
    if message.reply_to_message:
        return message.reply_to_message.from_user
    return None
