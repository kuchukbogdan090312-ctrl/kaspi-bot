from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from services.subscription_service import (
    get_plans, get_plan, get_active_subscription, create_subscription, deactivate_expired
)
from services.payment_service import get_setting
from keyboards.keyboards import (
    plans_kb, plan_detail_kb, confirm_purchase_kb, community_kb, main_menu_kb
)
from utils.helpers import fmt_price, fmt_date

router = Router()


@router.message(F.text == "📚 Подписки")
async def subscriptions_menu(message: Message):
    await deactivate_expired()
    plans = await get_plans()
    if not plans:
        await message.answer("Тарифы временно недоступны.")
        return
    community_name = await get_setting("community_name") or "Закрытое сообщество"
    await message.answer(
        f"📚 <b>Подписки на «{community_name}»</b>\n\n"
        "Выберите подходящий тариф:",
        reply_markup=plans_kb(plans),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "plans_list")
async def plans_list_cb(cb: CallbackQuery):
    await deactivate_expired()
    plans = await get_plans()
    community_name = await get_setting("community_name") or "Закрытое сообщество"
    await cb.message.edit_text(
        f"📚 <b>Подписки на «{community_name}»</b>\n\n"
        "Выберите подходящий тариф:",
        reply_markup=plans_kb(plans),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("plan:"))
async def plan_detail(cb: CallbackQuery, db_user: dict):
    plan_id = int(cb.data.split(":")[1])
    plan = await get_plan(plan_id)
    if not plan:
        await cb.answer("Тариф не найден", show_alert=True)
        return
    active = await get_active_subscription(cb.from_user.id)
    duration_text = "Навсегда ♾️" if plan["duration_days"] is None else f"{plan['duration_days']} дней"
    text = (
        f"{plan['emoji']} <b>{plan['name']}</b>\n\n"
        f"📝 {plan['description']}\n\n"
        f"⏳ Срок: <b>{duration_text}</b>\n"
        f"💰 Цена: <b>{fmt_price(plan['price'])}</b>\n\n"
        f"💳 Ваш баланс: <b>{fmt_price(db_user['balance'])}</b>"
    )
    await cb.message.edit_text(
        text,
        reply_markup=plan_detail_kb(plan_id, bool(active)),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("buy:"))
async def buy_plan(cb: CallbackQuery, db_user: dict):
    plan_id = int(cb.data.split(":")[1])
    plan = await get_plan(plan_id)
    if not plan:
        await cb.answer("Тариф не найден", show_alert=True)
        return

    if db_user["balance"] < plan["price"]:
        deficit = plan["price"] - db_user["balance"]
        await cb.answer(
            f"❌ Недостаточно средств. Не хватает {fmt_price(deficit)}",
            show_alert=True,
        )
        return

    text = (
        f"🛒 <b>Подтверждение покупки</b>\n\n"
        f"{plan['emoji']} Тариф: <b>{plan['name']}</b>\n"
        f"💰 Стоимость: <b>{fmt_price(plan['price'])}</b>\n"
        f"💳 Ваш баланс: <b>{fmt_price(db_user['balance'])}</b>\n"
        f"📊 Остаток после: <b>{fmt_price(db_user['balance'] - plan['price'])}</b>\n\n"
        "Подтвердить покупку?"
    )
    await cb.message.edit_text(
        text,
        reply_markup=confirm_purchase_kb(plan_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("confirm_buy:"))
async def confirm_buy(cb: CallbackQuery, db_user: dict):
    plan_id = int(cb.data.split(":")[1])
    try:
        sub = await create_subscription(cb.from_user.id, plan_id)
    except ValueError as e:
        await cb.answer(str(e), show_alert=True)
        return

    community_link = await get_setting("community_link") or "#"
    community_name = await get_setting("community_name") or "сообщество"

    plan = await get_plan(plan_id)
    expires_text = "Навсегда ♾️" if sub.get("expires_at") is None else fmt_date(sub["expires_at"])

    await cb.message.edit_text(
        f"🎉 <b>Подписка успешно оформлена!</b>\n\n"
        f"{plan['emoji']} Тариф: <b>{plan['name']}</b>\n"
        f"⏳ Действует до: <b>{expires_text}</b>\n\n"
        f"Нажмите кнопку ниже, чтобы войти в сообщество 👇",
        reply_markup=community_kb(community_link),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "noop")
async def noop(cb: CallbackQuery):
    await cb.answer()
