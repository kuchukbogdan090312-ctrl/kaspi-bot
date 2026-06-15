import aiosqlite
import os
from config import settings


async def init_db():
    os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                balance INTEGER DEFAULT 0,
                is_blocked INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                duration_days INTEGER,
                price INTEGER NOT NULL,
                description TEXT,
                emoji TEXT DEFAULT '🟢',
                is_active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (plan_id) REFERENCES plans(id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)

        # Seed default plans
        existing = await db.execute("SELECT COUNT(*) FROM plans")
        row = await existing.fetchone()
        if row[0] == 0:
            await db.executemany(
                "INSERT INTO plans (name, duration_days, price, description, emoji) VALUES (?, ?, ?, ?, ?)",
                [
                    ("1 месяц", 30, 2990, "Доступ к закрытому сообществу на 1 месяц", "🟢"),
                    ("3 месяца", 90, 7490, "Доступ к закрытому сообществу на 3 месяца", "🔵"),
                    ("6 месяцев", 180, 13990, "Доступ к закрытому сообществу на 6 месяцев", "🟣"),
                    ("12 месяцев", 365, 24990, "Доступ к закрытому сообществу на 12 месяцев", "🟠"),
                    ("Навсегда", None, 49990, "Пожизненный доступ к закрытому сообществу", "🔴"),
                ],
            )

        # Seed default settings
        default_settings = [
            ("kaspi_phone", settings.KASPI_PHONE),
            ("kaspi_qr_url", settings.KASPI_QR_URL),
            ("community_link", settings.COMMUNITY_LINK),
            ("community_name", "Закрытое сообщество"),
        ]
        for key, value in default_settings:
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value)
            )

        await db.commit()


async def get_db():
    return aiosqlite.connect(settings.DB_PATH)
