from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import List


# ── Main Menu ─────────────────────────────────────────────────────────────────

def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📚 Подписки")
    builder.button(text="💰 Баланс")
    builder.button(text="🛒 Мои подписки")
    builder.button(text="👤 Профиль")
    builder.button(text="ℹ️ Поддержка")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


# ── Plans ──────────────────────────────────────────────────────────────────────

def plans_kb(plans: List[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in plans:
        price_fmt = f"{plan['price']:,}".replace(",", " ")
        builder.button(
            text=f"{plan['emoji']} {plan['name']} — {price_fmt} ₸",
            callback_data=f"plan:{plan['id']}",
        )
    builder.adjust(1)
    return builder.as_markup()


def plan_detail_kb(plan_id: int, has_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not has_active:
        builder.button(text="🛒 Купить", callback_data=f"buy:{plan_id}")
    else:
        builder.button(text="✅ У вас есть активная подписка", callback_data="noop")
    builder.button(text="◀️ Назад к тарифам", callback_data="plans_list")
    builder.adjust(1)
    return builder.as_markup()


def confirm_purchase_kb(plan_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить покупку", callback_data=f"confirm_buy:{plan_id}")
    builder.button(text="❌ Отмена", callback_data="plans_list")
    builder.adjust(1)
    return builder.as_markup()


def community_kb(link: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Войти в сообщество", url=link)
    builder.adjust(1)
    return builder.as_markup()


# ── Balance / Payment ──────────────────────────────────────────────────────────

def topup_amounts_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for amount in [1000, 2000, 5000, 10000]:
        amt_fmt = f"{amount:,}".replace(",", " ")
        builder.button(text=f"{amt_fmt} ₸", callback_data=f"topup:{amount}")
    builder.adjust(2)
    return builder.as_markup()


def paid_confirmation_kb(payment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Я оплатил", callback_data=f"paid:{payment_id}")
    builder.button(text="❌ Отмена", callback_data="balance_menu")
    builder.adjust(1)
    return builder.as_markup()


def back_to_balance_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="balance_menu")
    builder.adjust(1)
    return builder.as_markup()


# ── My Subscriptions ──────────────────────────────────────────────────────────

def my_subs_kb(subs: List[dict], community_link: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sub in subs:
        if sub.get("is_active") and (sub.get("expires_at") is None or sub.get("expires_at", "") > ""):
            builder.button(
                text=f"🚀 Войти в сообщество ({sub['plan_name']})",
                url=community_link,
            )
    builder.adjust(1)
    return builder.as_markup()


# ── Admin Menu ─────────────────────────────────────────────────────────────────

def admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Пользователи", callback_data="admin:users")
    builder.button(text="💰 Финансы", callback_data="admin:finance")
    builder.button(text="📢 Рассылка", callback_data="admin:broadcast")
    builder.button(text="⚙️ Настройки", callback_data="admin:settings")
    builder.button(text="🎟 Тарифы", callback_data="admin:plans")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def admin_user_kb(telegram_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Выдать баланс", callback_data=f"admin_give:{telegram_id}")
    builder.button(text="➖ Снять баланс", callback_data=f"admin_take:{telegram_id}")
    builder.button(text="🚫 Заблокировать", callback_data=f"admin_block:{telegram_id}")
    builder.button(text="✅ Разблокировать", callback_data=f"admin_unblock:{telegram_id}")
    builder.button(text="◀️ Назад", callback_data="admin:users")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def admin_payment_kb(payment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data=f"adm_confirm:{payment_id}")
    builder.button(text="❌ Отклонить", callback_data=f"adm_reject:{payment_id}")
    builder.adjust(2)
    return builder.as_markup()


def admin_plans_kb(plans: List[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in plans:
        builder.button(
            text=f"{plan['emoji']} {plan['name']} — {plan['price']:,} ₸".replace(",", " "),
            callback_data=f"admin_plan:{plan['id']}",
        )
    builder.button(text="◀️ Назад", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()


def admin_plan_edit_kb(plan_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Изменить цену", callback_data=f"plan_edit_price:{plan_id}")
    builder.button(text="📝 Изменить описание", callback_data=f"plan_edit_desc:{plan_id}")
    builder.button(text="◀️ Назад", callback_data="admin:plans")
    builder.adjust(2, 1)
    return builder.as_markup()


def admin_settings_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Номер Kaspi", callback_data="setting:kaspi_phone")
    builder.button(text="🔗 Ссылка на сообщество", callback_data="setting:community_link")
    builder.button(text="🏷 Название сообщества", callback_data="setting:community_name")
    builder.button(text="◀️ Назад", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()
