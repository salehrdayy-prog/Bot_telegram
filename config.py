import os
import logging

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("UnlimitedBot")

# توکن ربات از GitHub Secrets
BOT_TOKEN = os.getenv("BOT_TOKEN")

# شناسه مالک ربات (اختیاری)
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# نام ربات
BOT_NAME = "UnlimitedBot"

# مسیر دیتابیس
DATABASE_PATH = os.getenv("DATABASE_PATH", "group_manager.db")

# تنظیمات ضدفلود
FLOOD_LIMIT = 5
FLOOD_TIME = 5

# تنظیمات اخطار
MAX_WARNINGS = 3

# تنظیمات خوشامدگویی
WELCOME_ENABLED = True

# منطقه زمانی
TIMEZONE = "Asia/Tehran"


if not BOT_TOKEN:
    logger.warning("BOT_TOKEN is not configured!")
