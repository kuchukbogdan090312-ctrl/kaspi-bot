import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, List
from config import settings


async def get_plans() -> List[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM plans WHERE is_active=1 ORDER BY id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_plan(plan_id: int) -> Optional[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM plans WHERE id=?", (plan_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_active_subscription(telegram_id: int) -> Optional[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT s.*, p.name as plan_name, p.emoji, p.duration_days
               FROM subscriptions s
               JOIN plans p ON s.plan_id = p.id
               JOIN users u ON s.user_id = u.id
               WHERE u.telegram_id=?
               AND s.is_active=1
               AND (s.expires_at IS NULL OR s.expires_at > datetime('now'))
               ORDER BY s.started_at DESC LIMIT 1""",
            (telegram_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_subscriptions(telegram_id: int) -> List[dict]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT s.*, p.name as plan_name, p.emoji, p.duration_days
               FROM subscriptions s
               JOIN plans p ON s.plan_id = p.id
               JOIN users u ON s.user_id = u.id
               WHERE u.telegram_id=?
               ORDER BY s.started_at DESC""",
            (telegram_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def create_subscription(telegram_id: int, plan_id: int) -> dict:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Get user
        cursor = await db.execute("SELECT id, balance FROM users WHERE telegram_id=?", (telegram_id,))
        user = await cursor.fetchone()
        if not user:
            raise ValueError("Пользователь не найден")

        # Get plan
        cursor = await db.execute("SELECT * FROM plans WHERE id=?", (plan_id,))
        plan = await cursor.fetchone()
        if not plan:
            raise ValueError("Тариф не найден")

        plan = dict(plan)

        if user["balance"] < plan["price"]:
            raise ValueError("Недостаточно средств на балансе")

        # Check existing active
        cursor = await db.execute(
            """SELECT id FROM subscriptions
               WHERE user_id=? AND is_active=1
               AND (expires_at IS NULL OR expires_at > datetime('now'))""",
            (user["id"],),
        )
        existing = await cursor.fetchone()
        if existing:
            raise ValueError("У вас уже есть активная подписка")

        # Calculate expiry
        if plan["duration_days"] is None:
            expires_at = None
        else:
            expires_at = (datetime.now() + timedelta(days=plan["duration_days"])).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        # Deduct balance
        await db.execute(
            "UPDATE users SET balance = balance - ? WHERE id=?",
            (plan["price"], user["id"]),
        )

        # Log transaction
        await db.execute(
            "INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)",
            (user["id"], -plan["price"], "debit", f"Покупка подписки: {plan['name']}"),
        )

        # Create subscription
        cursor = await db.execute(
            "INSERT INTO subscriptions (user_id, plan_id, expires_at) VALUES (?, ?, ?)",
            (user["id"], plan_id, expires_at),
        )
        sub_id = cursor.lastrowid

        await db.commit()

        cursor = await db.execute(
            """SELECT s.*, p.name as plan_name, p.emoji FROM subscriptions s
               JOIN plans p ON s.plan_id=p.id WHERE s.id=?""",
            (sub_id,),
        )
        return dict(await cursor.fetchone())


async def update_plan(plan_id: int, **kwargs):
    allowed = {"price", "description", "name"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k}=?" for k in fields)
    values = list(fields.values()) + [plan_id]
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(f"UPDATE plans SET {set_clause} WHERE id=?", values)
        await db.commit()


async def deactivate_expired():
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            """UPDATE subscriptions SET is_active=0
               WHERE is_active=1 AND expires_at IS NOT NULL AND expires_at <= datetime('now')"""
        )
        await db.commit()


async def get_stats() -> dict:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        total_users = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        active_subs = (
            await (
                await db.execute(
                    """SELECT COUNT(*) FROM subscriptions WHERE is_active=1
                       AND (expires_at IS NULL OR expires_at > datetime('now'))"""
                )
            ).fetchone()
        )[0]
        total_purchases = (
            await (
                await db.execute(
                    "SELECT COUNT(*) FROM transactions WHERE type='debit' AND description LIKE 'Покупка%'"
                )
            ).fetchone()
        )[0]
        total_revenue = (
            await (
                await db.execute(
                    "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='confirmed'"
                )
            ).fetchone()
        )[0]

        cursor = await db.execute(
            """SELECT p.name, p.emoji, COUNT(s.id) as count,
                      COALESCE(SUM(p.price), 0) as revenue
               FROM subscriptions s JOIN plans p ON s.plan_id=p.id
               GROUP BY p.id ORDER BY count DESC"""
        )
        plan_stats = [dict(r) for r in await cursor.fetchall()]

        return {
            "total_users": total_users,
            "active_subs": active_subs,
            "total_purchases": total_purchases,
            "total_revenue": total_revenue,
            "plan_stats": plan_stats,
        }
