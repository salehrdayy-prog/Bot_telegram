import re
from datetime import datetime, timedelta
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
    settings = get_group_settings(chat_id)
    
    if data == "panel_main":
        await query.edit_message_text("🎛 پنل مدیریت:", reply_markup=keyboards.main_panel())
    
    elif data == "panel_locks_main":
        await query.edit_message_text("🔒 قفل‌های اصلی:", reply_markup=keyboards.locks_panel_main(settings))
        
    elif data == "panel_locks_extra":
        await query.edit_message_text("🛡 قفل‌های تکمیلی:", reply_markup=keyboards.locks_panel_extra(settings))
    
    elif data.startswith("toggle_"):
        setting_name = data.replace("toggle_", "")
        
        if setting_name in settings:
            new_value = 0 if settings[setting_name] else 1
            update_group_setting(chat_id, setting_name, new_value)
            settings = get_group_settings(chat_id)
        
        # تشخیص اینکه در کدام صفحه هستیم تا کیبورد مناسب را برگردانیم
        if setting_name.startswith("lock_") and setting_name in ['lock_poll', 'lock_contact', 'lock_location', 'lock_game', 'lock_audio', 'lock_video_note', 'lock_voice_chat', 'lock_caption']:
            await query.edit_message_text("🛡 قفل‌های تکمیلی:", reply_markup=keyboards.locks_panel_extra(settings))
        elif setting_name.startswith("anti_"):
            await query.edit_message_text("🛡 قفل‌های تکمیلی:", reply_markup=keyboards.locks_panel_extra(settings))
        elif setting_name.startswith("welcome"):
            await query.edit_message_text("👋 تنظیمات خوش‌آمدگویی:", reply_markup=keyboards.welcome_panel(settings))
        else:
            await query.edit_message_text("🔒 قفل‌های اصلی:", reply_markup=keyboards.locks_panel_main(settings))

    elif data == "panel_welcome":
        await query.edit_message_text("👋 تنظیمات خوش‌آمدگویی:", reply_markup=keyboards.welcome_panel(settings))

    elif data == "change_welcome_text":
        await query.edit_message_text(
            "📝 لطفاً متن جدید خوش‌آمدگویی را با دستور زیر بفرستید:\n\n"
            "`تنظیم خوشامد [متن شما]`\n"
            "مثال: `تنظیم خوشامد سلام {name} عزیز!`",
            parse_mode="Markdown"
        )

    elif data == "panel_warns":
        text = f"⚠️ حداکثر اخطار: {settings['max_warns']}\n🔨 مجازات: {settings['warn_action']}\n\nبرای تغییر از دستورات استفاده کنید:\n`حداکثر اخطار [عدد]`"
        await query.edit_message_text(text, reply_markup=keyboards.main_panel(), parse_mode="Markdown")

    elif data == "panel_purge":
        await query.edit_message_text(
            "🧹 برای پاکسازی پیام‌ها، روی آخرین پیامی که می‌خواهید بماند ریپلای کنید و دستور `پاکسازی` را بزنید.",
            reply_markup=keyboards.main_panel()
        )

# ================= راهنما =================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 **راهنمای دستورات ربات**\n\n"
        "شما می‌توانید با کلیک روی دکمه‌های زیر، دستورات را کپی کنید:\n\n"
        "🔹 `اخطار` : اخطار به کاربر (با ریپلای)\n"
        "🔹 `سکوت 1h` : سکوت موقت (1h یعنی ۱ ساعت، 30m یعنی ۳۰ دقیقه)\n"
        "🔹 `پاکسازی` : پاکسازی پیام‌ها (با ریپلای)\n"
        "🔹 `تنظیم خوشامد متن` : تغییر متن خوش‌آمد\n"
        "🔹 `حداکثر اخطار 3` : تنظیم حداکثر اخطار\n\n"
        "🎛 برای باز کردن پنل مدیریت کلمه `پنل` را بفرستید."
    )
    await update.message.reply_text(help_text, reply_markup=keyboards.help_keyboard(), parse_mode="Markdown")

# ================= توابع با دستورات =================
async def change_welcome_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    # استخراج متن از پیام کاربر (بعد از کلمه "تنظیم خوشامد")
    text = update.message.text.replace("تنظیم خوشامد", "").strip()
    if not text:
        await update.message.reply_text("❗️ متن را وارد کنید. مثال: `تنظیم خوشامد سلام {name}`", parse_mode="Markdown")
        return
    update_group_setting(update.effective_chat.id, 'welcome_text', text)
    await update.message.reply_text("✅ متن خوش‌آمدگویی تغییر کرد.")

async def set_max_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    try:
        # استخراج عدد از پیام
        count = int(update.message.text.replace("حداکثر اخطار", "").strip())
        update_group_setting(update.effective_chat.id, 'max_warns', count)
        await update.message.reply_text(f"✅ حداکثر اخطار به {count} تغییر یافت.")
    except ValueError:
        await update.message.reply_text("❗️ یک عدد وارد کنید. مثال: `حداکثر اخطار 3`")

async def mute_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("❗️ روی پیام کاربر ریپلای کنید.")
        return
    try:
        # استخراج زمان از پیام (مثلا "سکوت 1h")
        time_str = update.message.text.replace("سکوت", "").strip()
        if not re.match(r"^\d+[hm]$", time_str):
            raise ValueError
        amount = int(time_str[:-1])
        unit = time_str[-1]
        seconds = amount * 3600 if unit == 'h' else amount * 60
        until_date = datetime.now() + timedelta(seconds=seconds)
        
        await context.bot.restrict_chat_member(
            update.effective_chat.id, target.id, 
            ChatPermissions(can_send_messages=False), 
            until_date=until_date
        )
        await update.message.reply_text(f"🔇 {target.mention_html()} برای {time_str} سکوت شد.", parse_mode="HTML")
    except ValueError:
        await update.message.reply_text("❗️ فرمت زمان اشتباه است. مثال: `سکوت 1h` یا `سکوت 30m`")

async def purge_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    message = update.effective_message
    if not message.reply_to_message:
        await message.reply_text("❗️ روی پیامی که می‌خواهید از آن به بعد پاک شود ریپلای کنید.")
        return
    
    start_id = message.reply_to_message.message_id
    end_id = message.message_id
    count = 0
    
    for msg_id in range(start_id, end_id + 1):
        try:
            await context.bot.delete_message(update.effective_chat.id, msg_id)
            count += 1
        except Exception:
            pass
    
    await message.reply_text(f"🧹 {count} پیام پاکسازی شد.")

# ================= توابع پایه =================
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
    await update.message.reply_text(f"⚠️ {target.mention_html()} اخطار گرفت. ({warns}/{max_warns})", parse_mode="HTML")
    if warns >= max_warns:
        if settings['warn_action'] == 'mute':
            await context.bot.restrict_chat_member(chat_id, target.id, ChatPermissions(can_send_messages=False))
            await update.message.reply_text(f"🔇 {target.mention_html()} سکوت شد.", parse_mode="HTML")
        else:
            await context.bot.ban_chat_member(chat_id, target.id)
            await update.message.reply_text(f"🚫 {target.mention_html()} بن شد.", parse_mode="HTML")
        reset_warns(chat_id, target.id)

async def reset_user_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if not target: return
    reset_warns(update.effective_chat.id, target.id)
    await update.message.reply_text(f"✅ اخطارهای {target.mention_html()} صفر شد.", parse_mode="HTML")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if not target: return
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, ChatPermissions(can_send_messages=False))
        await update.message.reply_text(f"🔇 {target.mention_html()} سکوت شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if not target: return
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        await update.message.reply_text(f"🔊 {target.mention_html()} رفع سکوت شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if not target: return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"🚫 {target.mention_html()} بن شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    target = await get_target_user(update, context)
    if not target: return
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"✅ {target.mention_html()} رفع بن شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")
