import aiosqlite
import os

from config import DATABASE_PATH


DB_PATH = DATABASE_PATH


# ==================================================
# AZRAEL LOCKS
# ==================================================

LOCKS = {
    "links": "لینک‌ها",
    "forwards": "پیام‌های فورواردی",
    "text": "پیام‌های متنی",
    "hashtags": "هشتگ‌ها",
    "mentions": "منشن‌ها",
    "phone_numbers": "شماره تلفن",
    "emojis": "ایموجی‌ها",
    "photos": "عکس‌ها",
    "videos": "ویدیوها",
    "gifs": "گیف‌ها",
    "stickers": "استیکرها",
    "voice": "پیام‌های صوتی",
    "video_notes": "ویدیو مسیج",
    "audio": "موزیک و فایل صوتی",
    "files": "فایل‌ها و اسناد",
    "contacts": "مخاطبین",
    "locations": "موقعیت مکانی",
    "polls": "نظرسنجی‌ها",
    "bots": "پیام ربات‌ها",
    "new_members": "پیام ورود اعضای جدید",
    "group_info": "تغییرات اطلاعات گروه",
    "group_photo": "تغییر عکس گروه",
    "poll_creation": "ساخت نظرسنجی",
    "service_messages": "پیام‌های سیستمی",
}


# ==================================================
# DATABASE MIGRATION
# ==================================================

async def migrate_groups_table(db):
    cursor = await db.execute("PRAGMA table_info(groups)")
    columns = await cursor.fetchall()

    column_names = {
        column[1].lower()
        for column in columns
    }

    if "group_id" not in column_names:

        await db.execute("""
            ALTER TABLE groups
            ADD COLUMN group_id INTEGER
        """)

        # تلاش برای بازیابی شناسه گروه از ستون‌های قدیمی
        candidates = (
            "chat_id",
            "telegram_chat_id",
            "telegram_id",
            "groupid",
        )

        old_column = next(
            (
                name for name in candidates
                if name in column_names
            ),
            None
        )

        if old_column:
            await db.execute(
                f"""
                UPDATE groups
                SET group_id = "{old_column}"
                WHERE group_id IS NULL
                """
            )

        elif "id" in column_names:
            # فقط شناسه‌های منفی، که معمولاً شناسه گروه تلگرام هستند
            await db.execute("""
                UPDATE groups
                SET group_id = id
                WHERE group_id IS NULL
                AND id < 0
            """)

    # اضافه کردن ستون‌های احتمالیِ موجود نبودن
    required_columns = {
        "title": "TEXT DEFAULT ''",
        "welcome_enabled": "INTEGER DEFAULT 1",
        "welcome_text": "TEXT DEFAULT 'سلام {name}، به گروه خوش آمدی!'",
        "rules": "TEXT DEFAULT ''",
        "created_at": "TEXT",
    }

    cursor = await db.execute("PRAGMA table_info(groups)")
    current_columns = {
        row[1].lower()
        for row in await cursor.fetchall()
    }

    for column, definition in required_columns.items():
        if column not in current_columns:
            await db.execute(
                f'ALTER TABLE groups ADD COLUMN "{column}" {definition}'
            )

    await db.execute("""
        UPDATE groups
        SET title = ''
        WHERE title IS NULL
    """)

    await db.execute("""
        UPDATE groups
        SET created_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL OR created_at = ''
    """)

    # جلوگیری از شناسه‌های تکراری
    await db.execute("""
        DELETE FROM groups
        WHERE group_id IS NOT NULL
        AND rowid NOT IN (
            SELECT MIN(rowid)
            FROM groups
            WHERE group_id IS NOT NULL
            GROUP BY group_id
        )
    """)

    await db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_groups_group_id
        ON groups(group_id)
        WHERE group_id IS NOT NULL
    """)


# ==================================================
# DATABASE INITIALIZATION
# ==================================================

async def init_db():

    os.makedirs(
        os.path.dirname(DB_PATH) or ".",
        exist_ok=True
    )

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                title TEXT DEFAULT '',
                welcome_enabled INTEGER DEFAULT 1,
                welcome_text TEXT DEFAULT 'سلام {name}، به گروه خوش آمدی!',
                rules TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await migrate_groups_table(db)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reason TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS locks (
                group_id INTEGER NOT NULL,
                lock_type TEXT NOT NULL,
                enabled INTEGER DEFAULT 0,
                PRIMARY KEY (group_id, lock_type)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                group_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT DEFAULT '',
                PRIMARY KEY (group_id, key)
            )
        """)

        await db.commit()


# ==================================================
# GROUP MANAGEMENT
# ==================================================

async def ensure_group(group_id: int, title: str = ""):

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
            INSERT OR IGNORE INTO groups (group_id, title)
            VALUES (?, ?)
        """, (group_id, title))

        if title:
            await db.execute("""
                UPDATE groups
                SET title = ?
                WHERE group_id = ?
            """, (title, group_id))

        await db.commit()


async def get_group(group_id: int):

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        cursor = await db.execute("""
            SELECT *
            FROM groups
            WHERE group_id = ?
        """, (group_id,))

        row = await cursor.fetchone()

        return dict(row) if row else None


# ==================================================
# GROUP SETTINGS
# ==================================================

async def set_group_setting(
    group_id: int,
    key: str,
    value: str
):

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
            INSERT INTO settings (group_id, key, value)
            VALUES (?, ?, ?)
            ON CONFLICT(group_id, key)
            DO UPDATE SET value = excluded.value
        """, (group_id, key, str(value)))

        await db.commit()


async def get_group_setting(
    group_id: int,
    key: str,
    default=None
):

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
            SELECT value
            FROM settings
            WHERE group_id = ? AND key = ?
        """, (group_id, key))

        row = await cursor.fetchone()

        return row[0] if row else default


# ==================================================
# WARNINGS
# ==================================================

async def add_warning(
    group_id: int,
    user_id: int,
    reason: str = ""
):

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
            INSERT INTO warnings (group_id, user_id, reason)
            VALUES (?, ?, ?)
        """, (group_id, user_id, reason))

        await db.commit()


async def get_warnings(
    group_id: int,
    user_id: int
):

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
            SELECT COUNT(*)
            FROM warnings
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))

        row = await cursor.fetchone()

        return row[0] if row else 0


async def reset_warnings(
    group_id: int,
    user_id: int
):

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
            DELETE FROM warnings
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))

        await db.commit()


# ==================================================
# LOCK MANAGEMENT
# ==================================================

async def set_lock(
    group_id: int,
    lock_type: str,
    enabled: bool
):

    if lock_type not in LOCKS:
        raise ValueError(f"Unknown lock type: {lock_type}")

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
            INSERT INTO locks (
                group_id,
                lock_type,
                enabled
            )
            VALUES (?, ?, ?)

            ON CONFLICT(group_id, lock_type)
            DO UPDATE SET enabled = excluded.enabled
        """, (
            group_id,
            lock_type,
            int(enabled)
        ))

        await db.commit()


async def get_lock(
    group_id: int,
    lock_type: str
) -> bool:

    if lock_type not in LOCKS:
        return False

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
            SELECT enabled
            FROM locks
            WHERE group_id = ?
            AND lock_type = ?
        """, (group_id, lock_type))

        row = await cursor.fetchone()

        return bool(row[0]) if row else False


async def get_locks(group_id: int) -> dict:

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
            SELECT lock_type, enabled
            FROM locks
            WHERE group_id = ?
        """, (group_id,))

        rows = await cursor.fetchall()

        saved_locks = {
            lock_type: bool(enabled)
            for lock_type, enabled in rows
        }

        return {
            lock_type: saved_locks.get(lock_type, False)
            for lock_type in LOCKS
        }


async def reset_locks(group_id: int):

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
            DELETE FROM locks
            WHERE group_id = ?
        """, (group_id,))

        await db.commit()
