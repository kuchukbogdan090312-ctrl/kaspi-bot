import aiosqlite
from config import settings
from typing import Optional, List


async def get_or_create_user(telegram_id: int, username: str = None, full_name: str = None) -> dict:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            """INSERT OR IGNORE INTO users (telegram_id, username, full_name)
               VALUES (?, ?, ?)""",
            (telegram_id, username, full_name),
        )
        await db.execute(
            """UPDATE users SET username=?, full_name=? WHERE telegram_id=?""",
            (username, full_name, telegram_id),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
        row = await cursor.fetchone()
        return dict(row)


async def get_user(telegram_id: int) -> Optional[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_by_id(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE id=?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_balance(telegram_id: int, amount: int, description: str = "Пополнение баланса"):
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE telegram_id=?",
            (amount, telegram_id),
        )
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id=?", (telegram_id,))
        row = await cursor.fetchone()
        if row:
            await db.execute(
                "INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)",
                (row[0], amount, "credit" if amount > 0 else "debit", description),
            )
        await db.commit()


async def block_user(telegram_id: int):
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute("UPDATE users SET is_blocked=1 WHERE telegram_id=?", (telegram_id,))
        await db.commit()


async def unblock_user(telegram_id: int):
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute("UPDATE users SET is_blocked=0 WHERE telegram_id=?", (telegram_id,))
        await db.commit()


async def get_all_users() -> List[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def search_user(query: str) -> Optional[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Try by telegram_id first
        try:
            tid = int(query)
            cursor = await db.execute("SELECT * FROM users WHERE telegram_id=?", (tid,))
        except ValueError:
            uname = query.lstrip("@")
            cursor = await db.execute("SELECT * FROM users WHERE username=?", (uname,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_transactions(telegram_id: int) -> List[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT t.* FROM transactions t
               JOIN users u ON t.user_id = u.id
               WHERE u.telegram_id=?
               ORDER BY t.created_at DESC LIMIT 20""",
            (telegram_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
