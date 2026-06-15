from datetime import datetime
from typing import Optional


def fmt_price(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " ₸"


def fmt_date(dt_str: Optional[str]) -> str:
    if not dt_str:
        return "Навсегда ♾️"
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return dt_str


def is_sub_active(sub: dict) -> bool:
    if not sub.get("is_active"):
        return False
    expires = sub.get("expires_at")
    if not expires:
        return True
    try:
        dt = datetime.strptime(expires, "%Y-%m-%d %H:%M:%S")
        return dt > datetime.now()
    except Exception:
        return False


def sub_status_text(sub: dict) -> str:
    if is_sub_active(sub):
        expires = sub.get("expires_at")
        if not expires:
            return "✅ Активна — Навсегда ♾️"
        return f"✅ Активна до {fmt_date(expires)}"
    return "❌ Истекла"
