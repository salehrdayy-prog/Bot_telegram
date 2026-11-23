import aiosqlite
import os

from config import DATABASE_PATH

DB_PATH = DATABASE_PATH


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

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


async def ensure_group(group_id: int, title: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO groups (group_id, title)
            VALUES (?, ?)
        """, (group_id, title))

        if title:
            await db.execute("""
                UPDATE groups SET title = ?
                WHERE group_id = ?
            """, (title, group_id))

        await db.commit()


async def get_group(group_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            "SELECT * FROM groups WHERE group_id = ?",
            (group_id,)
        )

        row = await cursor.fetchone()
        return dict(row) if row else None


async def set_group_setting(group_id: int, key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO settings (group_id, key, value)
            VALUES (?, ?, ?)
            ON CONFLICT(group_id, key)
            DO UPDATE SET value = excluded.value
        """, (group_id, key, str(value)))

        await db.commit()


async def get_group_setting(group_id: int, key: str, default=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT value FROM settings
            WHERE group_id = ? AND key = ?
        """, (group_id, key))

        row = await cursor.fetchone()
        return row[0] if row else default


async def add_warning(group_id: int, user_id: int, reason: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO warnings (group_id, user_id, reason)
            VALUES (?, ?, ?)
        """, (group_id, user_id, reason))

        await db.commit()


async def get_warnings(group_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT COUNT(*) FROM warnings
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))

        row = await cursor.fetchone()
        return row[0] if row else 0


async def reset_warnings(group_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            DELETE FROM warnings
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))

        await db.commit()


async def set_lock(group_id: int, lock_type: str, enabled: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO locks (group_id, lock_type, enabled)
            VALUES (?, ?, ?)
            ON CONFLICT(group_id, lock_type)
            DO UPDATE SET enabled = excluded.enabled
        """, (group_id, lock_type, int(enabled)))

        await db.commit()


async def get_lock(group_id: int, lock_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT enabled FROM locks
            WHERE group_id = ? AND lock_type = ?
        """, (group_id, lock_type))

        row = await cursor.fetchone()
        return bool(row[0]) if row else False
