import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from database import init_db
import handlers.admin as admin
import handlers.filters as filters_mod
import handlers.welcome as welcome_mod

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing! Set it in environment variables.")

    init_db()
    
    app = Application.builder().token(BOT_TOKEN).build()

    # پنل و دکمه‌ها
    app.add_handler(CommandHandler("panel", admin.panel_command))
    app.add_handler(CallbackQueryHandler(admin.panel_callback, pattern="^panel_|^toggle_lock_"))

    # دستورات مدیریتی
    app.add_handler(CommandHandler("warn", admin.warn_user))
    app.add_handler(CommandHandler("unwarn", admin.reset_user_warns))
    app.add_handler(CommandHandler("mute", admin.warn_user)) # می‌توانید منطق را جدا کنید
    app.add_handler(CommandHandler("unmute", admin.unmute_user))
    app.add_handler(CommandHandler("ban", admin.ban_user))
    app.add_handler(CommandHandler("unban", admin.unban_user))

    # فیلترها
    filter_group = filters.ChatType.GROUPS & ~filters.StatusUpdate.ALL
    app.add_handler(MessageHandler(filter_group, filters_mod.filter_messages))

    # خوش‌آمد و خداحافظ
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_mod.welcome_new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, welcome_mod.goodbye_member))

    print("✅ Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
