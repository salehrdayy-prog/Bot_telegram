import os
import logging

# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("AZRAEL")


# ==================================================
# BOT CONFIGURATION
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = int(os.getenv("OWNER_ID") or "0")

BOT_NAME = "AZRAEL"


# ==================================================
# DATABASE
# ==================================================

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "group_manager.db"
)


# ==================================================
# ANTI FLOOD
# ==================================================

FLOOD_LIMIT = 5
FLOOD_TIME = 5


# ==================================================
# WARNINGS
# ==================================================

MAX_WARNINGS = 3


# ==================================================
# WELCOME
# ==================================================

WELCOME_ENABLED = True


# ==================================================
# TIMEZONE
# ==================================================

TIMEZONE = "Asia/Tehran"


# ==================================================
# VALIDATION
# ==================================================

if not BOT_TOKEN:
    logger.warning("BOT_TOKEN is not configured!")
