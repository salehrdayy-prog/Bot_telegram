import sqlite3
import logging
import subprocess
import os
from config import DATABASE_FILE

log = logging.getLogger(__name__)

def get_connection():
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        # ستون‌های جدید برای مرحله ۳
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
                lock_voice INTEGER DEFAULT 0,
                lock_username INTEGER DEFAULT 0,
                lock_hashtag INTEGER DEFAULT 0,
                lock_bots INTEGER DEFAULT 0,
                lock_emoji INTEGER DEFAULT 0,
                anti_flood INTEGER DEFAULT 0,
                anti_repeat INTEGER DEFAULT 0,
                anti_bad_words INTEGER DEFAULT 0,
                lock_poll INTEGER DEFAULT 0,
                lock_contact INTEGER DEFAULT 0,
                lock_location INTEGER DEFAULT 0,
                lock_game INTEGER DEFAULT 0,
                lock_inline INTEGER DEFAULT 0,
                lock_forwarded_channel INTEGER DEFAULT 0,
                lock_url INTEGER DEFAULT 0,
                lock_tg_link INTEGER DEFAULT 0,
                lock_mention INTEGER DEFAULT 0,
                lock_nsfw INTEGER DEFAULT 0,
                max_flood INTEGER DEFAULT 5,
                flood_mute_time INTEGER DEFAULT 60,
                auto_delete_welcome INTEGER DEFAULT 0,
                welcome_delete_time INTEGER DEFAULT 60,
                auto_ban_warn INTEGER DEFAULT 0,
                warn_expiry_days INTEGER DEFAULT 30,
                lock_caption INTEGER DEFAULT 0,
                lock_reply INTEGER DEFAULT 0,
                lock_voice_chat INTEGER DEFAULT 0,
                lock_video_note INTEGER DEFAULT 0,
                lock_audio INTEGER DEFAULT 0,
                lock_gif_caption INTEGER DEFAULT 0,
                anti_spam INTEGER DEFAULT 0,
                anti_bot INTEGER DEFAULT 1,
                anti_channel INTEGER DEFAULT 0,
                anti_join_leave INTEGER DEFAULT 0,
                anti_unknown_command INTEGER DEFAULT 0,
                anti_cashtag INTEGER DEFAULT 0,
                anti_hashtag INTEGER DEFAULT 0,
                anti_mention INTEGER DEFAULT 0,
                anti_forward INTEGER DEFAULT 0,
                anti_photo INTEGER DEFAULT 0,
                anti_video INTEGER DEFAULT 0,
                anti_voice INTEGER DEFAULT 0,
                anti_document INTEGER DEFAULT 0,
                anti_sticker INTEGER DEFAULT 0,
                anti_gif INTEGER DEFAULT 0,
                anti_emoji INTEGER DEFAULT 0,
                anti_nsfw INTEGER DEFAULT 0,
                anti_link INTEGER DEFAULT 0,
                anti_username INTEGER DEFAULT 0,
                anti_caption_link INTEGER DEFAULT 0,
                anti_caption_username INTEGER DEFAULT 0,
                anti_caption_hashtag INTEGER DEFAULT 0,
                anti_caption_mention INTEGER DEFAULT 0,
                anti_caption_email INTEGER DEFAULT 0,
                anti_caption_phone INTEGER DEFAULT 0,
                anti_caption_bad_words INTEGER DEFAULT 0,
                anti_caption_emoji INTEGER DEFAULT 0,
                anti_email INTEGER DEFAULT 0,
                anti_phone INTEGER DEFAULT 0,
                anti_website INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER,
                user_id INTEGER,
                warns INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                chat_id INTEGER PRIMARY KEY,
                flood_count INTEGER DEFAULT 0,
                last_message_time TEXT
            )
        """)
        conn.commit()
    log.info("Database initialized.")

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
    # لیست تمام ستون‌های مجاز
    allowed = [
        'welcome_enabled', 'welcome_text', 'goodbye_enabled', 'goodbye_text',
        'max_warns', 'warn_action', 'lock_link', 'lock_forward', 'lock_sticker',
        'lock_gif', 'lock_photo', 'lock_video', 'lock_file', 'lock_voice',
        'lock_username', 'lock_hashtag', 'lock_bots', 'lock_emoji', 'anti_flood',
        'anti_repeat', 'anti_bad_words', 'lock_poll', 'lock_contact', 'lock_location',
        'lock_game', 'lock_inline', 'lock_forwarded_channel', 'lock_url', 'lock_tg_link',
        'lock_mention', 'lock_nsfw', 'max_flood', 'flood_mute_time', 'auto_delete_welcome',
        'welcome_delete_time', 'auto_ban_warn', 'warn_expiry_days', 'lock_caption',
        'lock_reply', 'lock_voice_chat', 'lock_video_note', 'lock_audio', 'lock_gif_caption',
        'anti_spam', 'anti_bot', 'anti_channel', 'anti_join_leave', 'anti_unknown_command',
        'anti_cashtag', 'anti_hashtag', 'anti_mention', 'anti_forward', 'anti_photo',
        'anti_video', 'anti_voice', 'anti_document', 'anti_sticker', 'anti_gif',
        'anti_emoji', 'anti_nsfw', 'anti_link', 'anti_username', 'anti_caption_link',
        'anti_caption_username', 'anti_caption_hashtag', 'anti_caption_mention',
        'anti_caption_email', 'anti_caption_phone', 'anti_caption_bad_words',
        'anti_caption_emoji', 'anti_email', 'anti_phone', 'anti_website'
    ]
    if setting not in allowed:
        raise ValueError("Invalid setting")
    with get_connection() as conn:
        cursor = conn.cursor()
        get_group_settings(chat_id)
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

def backup_database_to_github():
    try:
        gh_token = os.getenv("GH_TOKEN")
        repo_url = os.getenv("GITHUB_REPO_URL")
        if not gh_token or not repo_url:
            return
        subprocess.run(["git", "config", "user.name", "GitHub Action"], check=True)
        subprocess.run(["git", "config", "user.email", "action@github.com"], check=True)
        subprocess.run(["git", "add", DATABASE_FILE], check=True)
        result = subprocess.run(["git", "diff", "--cached", "--quiet"])
        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Auto backup database"], check=True)
            subprocess.run(
                ["git", "push", f"https://x-access-token:{gh_token}@github.com/{repo_url}.git", "HEAD:main"],
                check=True
            )
            log.info("✅ Database backed up.")
    except Exception as e:
        log.error("Backup error: %s", e)
