import aiosqlite
from typing import List, Optional
from config import settings


async def create_payment(telegram_id: int, amount: int) -> int:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id=?", (telegram_id,))
        user = await cursor.fetchone()
        if not user:
            raise ValueError("Пользователь не найден")
        cursor = await db.execute(
            "INSERT INTO payments (user_id, amount, status) VALUES (?, ?, 'pending')",
            (user[0], amount),
        )
        payment_id = cursor.lastrowid
        await db.commit()
        return payment_id


async def get_payment(payment_id: int) -> Optional[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT p.*, u.telegram_id, u.username, u.full_name
               FROM payments p JOIN users u ON p.user_id=u.id
               WHERE p.id=?""",
            (payment_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def confirm_payment(payment_id: int) -> dict:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT p.*, u.telegram_id FROM payments p JOIN users u ON p.user_id=u.id WHERE p.id=?",
            (payment_id,),
        )
        payment = await cursor.fetchone()
        if not payment:
            raise ValueError("Платёж не найден")
        payment = dict(payment)
        if payment["status"] != "pending":
            raise ValueError("Платёж уже обработан")

        await db.execute(
            "UPDATE payments SET status='confirmed', confirmed_at=datetime('now') WHERE id=?",
            (payment_id,),
        )
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE telegram_id=?",
            (payment["amount"], payment["telegram_id"]),
        )
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id=?", (payment["telegram_id"],))
        user_row = await cursor.fetchone()
        await db.execute(
            "INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)",
            (user_row[0], payment["amount"], "credit", f"Пополнение баланса (платёж #{payment_id})"),
        )
        await db.commit()
        return payment


async def reject_payment(payment_id: int) -> dict:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT p.*, u.telegram_id FROM payments p JOIN users u ON p.user_id=u.id WHERE p.id=?",
            (payment_id,),
        )
        payment = await cursor.fetchone()
        if not payment:
            raise ValueError("Платёж не найден")
        payment = dict(payment)
        if payment["status"] != "pending":
            raise ValueError("Платёж уже обработан")
        await db.execute("UPDATE payments SET status='rejected' WHERE id=?", (payment_id,))
        await db.commit()
        return payment


async def get_pending_payments() -> List[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT p.*, u.telegram_id, u.username, u.full_name
               FROM payments p JOIN users u ON p.user_id=u.id
               WHERE p.status='pending' ORDER BY p.created_at DESC"""
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_setting(key: str) -> str:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        cursor = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else ""


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
        await db.commit()
