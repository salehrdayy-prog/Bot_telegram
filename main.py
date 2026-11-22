import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters,
)

from config import BOT_TOKEN
from database import init_db, backup_database_to_github
import handlers.admin as admin
import handlers.filters as filters_mod
import handlers.welcome as welcome_mod

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

async def backup_job(context):
    backup_database_to_github()

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing!")

    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # ================= پنل =================
    app.add_handler(CommandHandler("panel", admin.panel_command))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^پنل$'), admin.panel_command))
    
    # ================= راهنما =================
    app.add_handler(CommandHandler("help", admin.help_command))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^راهنما$'), admin.help_command))

    # ================= دکمه‌های شیشه‌ای =================
    app.add_handler(CallbackQueryHandler(admin.panel_callback, pattern=r"^(panel_|toggle_)"))

    # ================= دستورات انگلیسی =================
    app.add_handler(CommandHandler("warn", admin.warn_user))
    app.add_handler(CommandHandler("unwarn", admin.reset_user_warns))
    app.add_handler(CommandHandler("mute", admin.mute_user))
    app.add_handler(CommandHandler("unmute", admin.unmute_user))
    app.add_handler(CommandHandler("ban", admin.ban_user))
    app.add_handler(CommandHandler("unban", admin.unban_user))
    app.add_handler(CommandHandler("setmaxwarns", admin.set_max_warns))
    app.add_handler(CommandHandler("setwelcome", admin.change_welcome_text))
    app.add_handler(CommandHandler("mutetime", admin.mute_time))
    app.add_handler(CommandHandler("purge", admin.purge_messages))

    # ================= دستورات فارسی (بدون اسلش) =================
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^اخطار$'), admin.warn_user))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^حذف اخطار$'), admin.reset_user_warns))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^سکوت$'), admin.mute_user))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^رفع سکوت$'), admin.unmute_user))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^بن$'), admin.ban_user))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^رفع بن$'), admin.unban_user))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^پاکسازی$'), admin.purge_messages))
    # برای دستورات پارامتری، باید از اسلش انگلیسی استفاده کرد یا با Regex پیچیده‌تر پیاده‌سازی کرد.

    # ================= فیلترها =================
    filter_group = filters.ChatType.GROUPS & ~filters.StatusUpdate.ALL
    app.add_handler(MessageHandler(filter_group, filters_mod.filter_messages))

    # ================= خوش‌آمد =================
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_mod.welcome_new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, welcome_mod.goodbye_member))

    # ================= بکاپ خودکار =================
    if app.job_queue:
        app.job_queue.run_repeating(backup_job, interval=600, first=30)

    log.info("✅ Bot is running with Phase 3...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
