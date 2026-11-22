import sqlite3
import logging
import subprocess
import os

from config import DATABASE_FILE

log = logging.getLogger(__name__)

# آدرس مخزن گیت‌هاب شما (باید جایگزین شود)
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "USERNAME/REPO")


def get_connection():
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                welcome_enabled INTEGER DEFAULT 0,
                welcome_text TEXT DEFAULT 'سلام {name}! خوش آمدی.',
                goodbye_enabled INTEGER DEFAULT 0,
                goodbye_text TEXT DEFAULT 'خداحافظ {name}!',
                max_warns INTEGER DEFAULT 3,
                warn_action TEXT DEFAULT 'mute',
                lock_link INTEGER DEFAULT 0,
                lock_forward INTEGER DEFAULT 0,
                lock_sticker INTEGER DEFAULT 0,
                lock_gif INTEGER DEFAULT 0,
                lock_photo INTEGER DEFAULT 0,
                lock_video INTEGER DEFAULT 0,
                lock_file INTEGER DEFAULT 0,
                lock_voice INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER,
                user_id INTEGER,
                warns INTEGER DEFAULT 0,
                is_muted INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        conn.commit()

    log.info("Database initialized successfully.")


def get_group_settings(chat_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM groups WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()

        if not row:
            cursor.execute("INSERT INTO groups (chat_id) VALUES (?)", (chat_id,))
            conn.commit()
            cursor.execute("SELECT * FROM groups WHERE chat_id = ?", (chat_id,))
            row = cursor.fetchone()

        return dict(row)


def update_group_setting(chat_id, setting, value):
    allowed_settings = [
        'welcome_enabled', 'welcome_text', 'goodbye_enabled', 'goodbye_text',
        'max_warns', 'warn_action', 'lock_link', 'lock_forward', 'lock_sticker',
        'lock_gif', 'lock_photo', 'lock_video', 'lock_file', 'lock_voice'
    ]

    if setting not in allowed_settings:
        raise ValueError("Invalid setting")

    with get_connection() as conn:
        cursor = conn.cursor()
        get_group_settings(chat_id)  # اطمینان از وجود گروه
        cursor.execute(f"UPDATE groups SET {setting} = ? WHERE chat_id = ?", (value, chat_id))
        conn.commit()


def get_user_warns(chat_id, user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT warns FROM users WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        row = cursor.fetchone()
        return row['warns'] if row else 0


def add_warn(chat_id, user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (chat_id, user_id, warns) VALUES (?, ?, 1)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET warns = warns + 1
        """, (chat_id, user_id))
        conn.commit()
        return get_user_warns(chat_id, user_id)


def reset_warns(chat_id, user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET warns = 0 WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        conn.commit()


# ==================================================
# بکاپ‌گیری خودکار دیتابیس روی گیت‌هاب
# ==================================================
def backup_database_to_github():
    try:
        gh_token = os.getenv("GH_TOKEN")
        if not gh_token:
            log.warning("GH_TOKEN is not set, skipping database backup.")
            return

        subprocess.run(["git", "config", "user.name", "GitHub Action"], check=True)
        subprocess.run(["git", "config", "user.email", "action@github.com"], check=True)
        subprocess.run(["git", "add", DATABASE_FILE], check=True)

        result = subprocess.run(["git", "diff", "--cached", "--quiet"])
        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Auto backup database"], check=True)
            subprocess.run(
                [
                    "git", "push",
                    f"https://x-access-token:{gh_token}@github.com/{GITHUB_REPO_URL}.git",
                    "HEAD:main"
                ],
                check=True
            )
            log.info("✅ Database backed up to GitHub")
        else:
            log.info("No changes in database, skipping backup.")

    except subprocess.CalledProcessError as e:
        log.error("❌ Git backup failed: %s", e)
    except Exception as e:
        log.error("❌ Backup error: %s", e)
