from telegram import Update
from telegram.ext import ContextTypes
from database import get_group_settings

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    if not message or not message.new_chat_members:
        return

    settings = get_group_settings(chat.id)
    if not settings['welcome_enabled']:
        return

    for member in message.new_chat_members:
        text = settings['welcome_text'].replace("{name}", member.first_name or "کاربر")
        await message.reply_text(text)

async def goodbye_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    if not message or not message.left_chat_member:
        return

    settings = get_group_settings(chat.id)
    if not settings['goodbye_enabled']:
        return

    member = message.left_chat_member
    text = settings['goodbye_text'].replace("{name}", member.first_name or "کاربر")
    await message.reply_text(text)
