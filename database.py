import sqlite3
import logging
from config import DATABASE_FILE

log = logging.getLogger(__name__)

def get_connection():
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # جدول تنظیمات گروه
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
        
        # جدول هشدارها و کاربران
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
    with get_connection() as conn:
        cursor = conn.cursor()
        # اطمینان از وجود گروه
        get_group_settings(chat_id)
        # استفاده از نام ستون به صورت امن (لیست سفید)
        allowed_settings = [
            'welcome_enabled', 'welcome_text', 'goodbye_enabled', 'goodbye_text',
            'max_warns', 'warn_action', 'lock_link', 'lock_forward', 'lock_sticker',
            'lock_gif', 'lock_photo', 'lock_video', 'lock_file', 'lock_voice'
        ]
        if setting not in allowed_settings:
            raise ValueError("Invalid setting")
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
        cursor.execute("INSERT INTO users (chat_id, user_id, warns) VALUES (?, ?, 1) ON CONFLICT(chat_id, user_id) DO UPDATE SET warns = warns + 1", (chat_id, user_id))
        conn.commit()
        return get_user_warns(chat_id, user_id)

def reset_warns(chat_id, user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET warns = 0 WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        conn.commit()
