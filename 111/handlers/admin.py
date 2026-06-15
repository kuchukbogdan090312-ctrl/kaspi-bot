from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import settings
from services.user_service import (
    get_all_users, search_user, update_balance, block_user,
    unblock_user, get_user_transactions
)
from services.subscription_service import (
    get_stats, get_user_subscriptions, get_plans, get_plan, update_plan,
    deactivate_expired
)
from services.payment_service import (
    confirm_payment, reject_payment, get_payment, get_setting, set_setting
)
from keyboards.keyboards import (
    admin_menu_kb, admin_user_kb, admin_plans_kb, admin_plan_edit_kb,
    admin_settings_kb, cancel_kb
)
from utils.states import AdminStates
from utils.helpers import fmt_price, fmt_date, is_sub_active

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


# ── /admin entry ──────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    await message.answer(
        "🔐 <b>Панель администратора</b>\n\nВыберите раздел:",
        reply_markup=admin_menu_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_back")
async def admin_back(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    await cb.message.edit_text(
        "🔐 <b>Панель администратора</b>\n\nВыберите раздел:",
        reply_markup=admin_menu_kb(),
        parse_mode="HTML",
    )


# ── Finance Stats ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:finance")
async def admin_finance(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    await deactivate_expired()
    stats = await get_stats()
    lines = [
        "💰 <b>Финансовая статистика</b>\n",
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>",
        f"🎟 Активных подписок: <b>{stats['active_subs']}</b>",
        f"🛒 Всего покупок: <b>{stats['total_purchases']}</b>",
        f"💵 Общий доход: <b>{fmt_price(stats['total_revenue'])}</b>\n",
        "📊 <b>По тарифам:</b>",
    ]
    for ps in stats["plan_stats"]:
        lines.append(f"  {ps['emoji']} {ps['name']}: {ps['count']} покупок — {fmt_price(ps['revenue'])}")

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_back")
    await cb.message.edit_text(
        "\n".join(lines), reply_markup=builder.as_markup(), parse_mode="HTML"
    )


# ── Users ─────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:users")
async def admin_users(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    await state.set_state(AdminStates.search_user)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="admin_back")
    await cb.message.edit_text(
        "👥 <b>Поиск пользователя</b>\n\n"
        "Введите Telegram ID или username (с @ или без):",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.message(AdminStates.search_user)
async def admin_search_user(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    user = await search_user(message.text.strip())
    if not user:
        await message.answer("❌ Пользователь не найден. Попробуйте снова.")
        return

    await state.clear()
    subs = await get_user_subscriptions(user["telegram_id"])
    active_subs = [s for s in subs if is_sub_active(s)]
    txs = await get_user_transactions(user["telegram_id"])

    uname = f"@{user['username']}" if user.get("username") else "нет"
    text = (
        f"👤 <b>Пользователь</b>\n\n"
        f"🆔 ID: <code>{user['telegram_id']}</code>\n"
        f"👤 Имя: {user.get('full_name', '—')}\n"
        f"🔗 Username: {uname}\n"
        f"💰 Баланс: <b>{fmt_price(user['balance'])}</b>\n"
        f"🚫 Заблокирован: {'Да' if user['is_blocked'] else 'Нет'}\n"
        f"🎟 Активных подписок: {len(active_subs)}\n"
        f"📅 Регистрация: {fmt_date(user.get('created_at', ''))}\n\n"
    )
    if txs:
        text += "📋 <b>Последние транзакции:</b>\n"
        for tx in txs[:5]:
            sign = "+" if tx["amount"] > 0 else ""
            text += f"  {sign}{fmt_price(tx['amount'])} — {tx.get('description', '')}\n"

    await message.answer(text, reply_markup=admin_user_kb(user["telegram_id"]), parse_mode="HTML")


# ── Give / Take balance ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_give:"))
async def admin_give_start(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    tid = int(cb.data.split(":")[1])
    await state.update_data(target_id=tid)
    await state.set_state(AdminStates.give_balance_amount)
    await cb.message.answer(
        f"💰 Введите сумму для начисления пользователю <code>{tid}</code>:",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.message(AdminStates.give_balance_amount)
async def admin_give_amount(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную положительную сумму.")
        return

    data = await state.get_data()
    target_id = data["target_id"]
    await update_balance(target_id, amount, f"Начислено администратором")
    await state.clear()
    await message.answer(f"✅ Начислено <b>{fmt_price(amount)}</b> пользователю <code>{target_id}</code>", parse_mode="HTML")
    try:
        await bot.send_message(
            target_id,
            f"💰 На ваш баланс начислено <b>{fmt_price(amount)}</b> администратором.",
            parse_mode="HTML",
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin_take:"))
async def admin_take_start(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    tid = int(cb.data.split(":")[1])
    await state.update_data(target_id=tid)
    await state.set_state(AdminStates.take_balance_amount)
    await cb.message.answer(
        f"➖ Введите сумму для снятия с пользователя <code>{tid}</code>:",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.message(AdminStates.take_balance_amount)
async def admin_take_amount(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную положительную сумму.")
        return

    data = await state.get_data()
    target_id = data["target_id"]
    await update_balance(target_id, -amount, "Снято администратором")
    await state.clear()
    await message.answer(f"✅ Снято <b>{fmt_price(amount)}</b> с пользователя <code>{target_id}</code>", parse_mode="HTML")


# ── Block / Unblock ───────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_block:"))
async def admin_block(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    tid = int(cb.data.split(":")[1])
    await block_user(tid)
    await cb.answer(f"🚫 Пользователь {tid} заблокирован", show_alert=True)


@router.callback_query(F.data.startswith("admin_unblock:"))
async def admin_unblock(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    tid = int(cb.data.split(":")[1])
    await unblock_user(tid)
    await cb.answer(f"✅ Пользователь {tid} разблокирован", show_alert=True)


# ── Payment confirm/reject ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_confirm:"))
async def adm_confirm_payment(cb: CallbackQuery, bot: Bot):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    payment_id = int(cb.data.split(":")[1])
    try:
        payment = await confirm_payment(payment_id)
    except ValueError as e:
        await cb.answer(str(e), show_alert=True)
        return

    await cb.message.edit_text(
        cb.message.text + f"\n\n✅ <b>Подтверждено администратором</b>",
        parse_mode="HTML",
    )
    try:
        await bot.send_message(
            payment["telegram_id"],
            f"✅ <b>Пополнение подтверждено!</b>\n\n"
            f"На ваш баланс зачислено <b>{fmt_price(payment['amount'])}</b>.",
            parse_mode="HTML",
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_reject:"))
async def adm_reject_payment(cb: CallbackQuery, bot: Bot):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    payment_id = int(cb.data.split(":")[1])
    try:
        payment = await reject_payment(payment_id)
    except ValueError as e:
        await cb.answer(str(e), show_alert=True)
        return

    await cb.message.edit_text(
        cb.message.text + f"\n\n❌ <b>Отклонено администратором</b>",
        parse_mode="HTML",
    )
    try:
        await bot.send_message(
            payment["telegram_id"],
            f"❌ <b>Пополнение отклонено</b>\n\n"
            f"Заявка на <b>{fmt_price(payment['amount'])}</b> была отклонена администратором.\n"
            "Обратитесь в поддержку если считаете это ошибкой.",
            parse_mode="HTML",
        )
    except Exception:
        pass


# ── Broadcast ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_menu(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    await state.set_state(AdminStates.broadcast_text)
    await cb.message.edit_text(
        "📢 <b>Рассылка</b>\n\nОтправьте текст рассылки (или фото с подписью):",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.message(AdminStates.broadcast_text)
async def admin_do_broadcast(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    users = await get_all_users()
    sent, failed = 0, 0

    for user in users:
        try:
            if message.photo:
                await bot.send_photo(
                    user["telegram_id"],
                    message.photo[-1].file_id,
                    caption=message.caption or "",
                    parse_mode="HTML",
                )
            else:
                await bot.send_message(
                    user["telegram_id"],
                    message.text or "",
                    parse_mode="HTML",
                )
            sent += 1
        except Exception:
            failed += 1

    await message.answer(
        f"📢 Рассылка завершена:\n✅ Отправлено: {sent}\n❌ Ошибок: {failed}"
    )


# ── Plans management ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:plans")
async def admin_plans(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    plans = await get_plans()
    await cb.message.edit_text(
        "🎟 <b>Управление тарифами</b>\n\nВыберите тариф для редактирования:",
        reply_markup=admin_plans_kb(plans),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin_plan:"))
async def admin_plan_detail(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    plan_id = int(cb.data.split(":")[1])
    plan = await get_plan(plan_id)
    if not plan:
        await cb.answer("Тариф не найден")
        return
    duration = "Навсегда" if plan["duration_days"] is None else f"{plan['duration_days']} дней"
    text = (
        f"{plan['emoji']} <b>{plan['name']}</b>\n\n"
        f"💰 Цена: {fmt_price(plan['price'])}\n"
        f"⏳ Срок: {duration}\n"
        f"📝 Описание: {plan['description']}"
    )
    await cb.message.edit_text(text, reply_markup=admin_plan_edit_kb(plan_id), parse_mode="HTML")


@router.callback_query(F.data.startswith("plan_edit_price:"))
async def plan_edit_price(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    plan_id = int(cb.data.split(":")[1])
    await state.update_data(edit_plan_id=plan_id)
    await state.set_state(AdminStates.edit_plan_price)
    await cb.message.answer(
        "💰 Введите новую цену в тенге (только число):",
        reply_markup=cancel_kb(),
    )


@router.message(AdminStates.edit_plan_price)
async def save_plan_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        price = int(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену.")
        return
    data = await state.get_data()
    await update_plan(data["edit_plan_id"], price=price)
    await state.clear()
    await message.answer(f"✅ Цена обновлена: <b>{fmt_price(price)}</b>", parse_mode="HTML")


@router.callback_query(F.data.startswith("plan_edit_desc:"))
async def plan_edit_desc(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    plan_id = int(cb.data.split(":")[1])
    await state.update_data(edit_plan_id=plan_id)
    await state.set_state(AdminStates.edit_plan_desc)
    await cb.message.answer("📝 Введите новое описание тарифа:", reply_markup=cancel_kb())


@router.message(AdminStates.edit_plan_desc)
async def save_plan_desc(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    await update_plan(data["edit_plan_id"], description=message.text.strip())
    await state.clear()
    await message.answer("✅ Описание обновлено.")


# ── Settings management ───────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:settings")
async def admin_settings(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    kaspi = await get_setting("kaspi_phone")
    link = await get_setting("community_link")
    name = await get_setting("community_name")
    text = (
        f"⚙️ <b>Настройки</b>\n\n"
        f"📱 Kaspi: <code>{kaspi or 'не задан'}</code>\n"
        f"🔗 Ссылка: <code>{link or 'не задана'}</code>\n"
        f"🏷 Название: {name or 'не задано'}"
    )
    await cb.message.edit_text(text, reply_markup=admin_settings_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("setting:"))
async def edit_setting(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer()
        return
    key = cb.data.split(":")[1]
    labels = {
        "kaspi_phone": "номер Kaspi",
        "community_link": "ссылку на сообщество",
        "community_name": "название сообщества",
    }
    await state.update_data(setting_key=key)
    await state.set_state(AdminStates.edit_setting)
    await cb.message.answer(
        f"✏️ Введите новое значение для «{labels.get(key, key)}»:",
        reply_markup=cancel_kb(),
    )


@router.message(AdminStates.edit_setting)
async def save_setting(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    await set_setting(data["setting_key"], message.text.strip())
    await state.clear()
    await message.answer("✅ Настройка сохранена.")
