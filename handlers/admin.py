from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from database import *
from utils import is_admin, get_target_user
import keyboards

async def panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("⛔️ فقط ادمین‌ها دسترسی دارند.")
        return
    await update.message.reply_text("🎛 پنل مدیریت:", reply_markup=keyboards.main_panel())

async def panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not await is_admin(update, context):
        await query.edit_message_text("⛔️ فقط ادمین‌ها دسترسی دارند.")
        return

    chat_id = update.effective_chat.id
    data = query.data
    
    if data == "panel_main":
        await query.edit_message_text("🎛 پنل مدیریت:", reply_markup=keyboards.main_panel())
    
    elif data == "panel_locks":
        settings = get_group_settings(chat_id)
        await query.edit_message_text("🔒 تنظیمات قفل‌ها:", reply_markup=keyboards.locks_panel(settings))
    
    elif data.startswith("toggle_lock_"):
        setting_name = data.replace("toggle_lock_", "")
        settings = get_group_settings(chat_id)
        new_value = 0 if settings[setting_name] else 1
        update_group_setting(chat_id, setting_name, new_value)
        
        settings = get_group_settings(chat_id)
        await query.edit_message_text("🔒 تنظیمات قفل‌ها:", reply_markup=keyboards.locks_panel(settings))

# ================= دستورات کاربر =================

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("❗️ روی پیام کاربر ریپلای کنید.")
        return
    
    chat_id = update.effective_chat.id
    warns = add_warn(chat_id, target.id)
    settings = get_group_settings(chat_id)
    max_warns = settings['max_warns']
    
    await update.message.reply_text(f"⚠️ کاربر {target.mention_html()} اخطار دریافت کرد. ({warns}/{max_warns})", parse_mode="HTML")
    
    if warns >= max_warns:
        if settings['warn_action'] == 'mute':
            await context.bot.restrict_chat_member(chat_id, target.id, ChatPermissions(can_send_messages=False))
            await update.message.reply_text(f"🔇 کاربر {target.mention_html()} به دلیل رسیدن به حداکثر اخطار سکوت شد.", parse_mode="HTML")
        else:
            await context.bot.ban_chat_member(chat_id, target.id)
            await update.message.reply_text(f"🚫 کاربر {target.mention_html()} به دلیل رسیدن به حداکثر اخطار بن شد.", parse_mode="HTML")
        reset_warns(chat_id, target.id)

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if not target: return
    chat_id = update.effective_chat.id
    try:
        await context.bot.restrict_chat_member(chat_id, target.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        await update.message.reply_text(f"🔊 کاربر {target.mention_html()} از سکوت خارج شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if not target: return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"🚫 کاربر {target.mention_html()} بن شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if not target: return
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"✅ کاربر {target.mention_html()} از بن خارج شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def reset_user_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if not target: return
    reset_warns(update.effective_chat.id, target.id)
    await update.message.reply_text(f"✅ اخطارهای کاربر {target.mention_html()} صفر شد.", parse_mode="HTML")
