from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from services.payment_service import (
    create_payment, get_payment, confirm_payment, reject_payment, get_setting
)
from keyboards.keyboards import (
    topup_amounts_kb, paid_confirmation_kb, back_to_balance_kb, admin_payment_kb
)
from utils.helpers import fmt_price
from config import settings

router = Router()


@router.message(F.text == "💰 Баланс")
async def balance_menu(message: Message, db_user: dict):
    text = (
        f"💰 <b>Ваш баланс</b>\n\n"
        f"💳 Доступно: <b>{fmt_price(db_user['balance'])}</b>\n\n"
        "Выберите сумму пополнения:"
    )
    await message.answer(text, reply_markup=topup_amounts_kb(), parse_mode="HTML")


@router.callback_query(F.data == "balance_menu")
async def balance_menu_cb(cb: CallbackQuery, db_user: dict):
    text = (
        f"💰 <b>Ваш баланс</b>\n\n"
        f"💳 Доступно: <b>{fmt_price(db_user['balance'])}</b>\n\n"
        "Выберите сумму пополнения:"
    )
    await cb.message.edit_text(text, reply_markup=topup_amounts_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("topup:"))
async def topup_select(cb: CallbackQuery):
    amount = int(cb.data.split(":")[1])
    kaspi_phone = await get_setting("kaspi_phone") or settings.KASPI_PHONE
    kaspi_qr = await get_setting("kaspi_qr_url") or settings.KASPI_QR_URL

    payment_id = await create_payment(cb.from_user.id, amount)

    text = (
        f"💳 <b>Пополнение баланса</b>\n\n"
        f"Сумма к оплате: <b>{fmt_price(amount)}</b>\n\n"
        f"📱 Номер Kaspi: <code>{kaspi_phone}</code>\n\n"
        f"Переведите <b>{fmt_price(amount)}</b> на указанный номер и нажмите кнопку «Я оплатил»"
    )
    kb = paid_confirmation_kb(payment_id)

    if kaspi_qr:
        try:
            await cb.message.answer_photo(
                kaspi_qr,
                caption=text,
                reply_markup=kb,
                parse_mode="HTML",
            )
            await cb.message.delete()
        except Exception:
            await cb.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("paid:"))
async def user_paid(cb: CallbackQuery, bot: Bot):
    payment_id = int(cb.data.split(":")[1])
    payment = await get_payment(payment_id)
    if not payment:
        await cb.answer("Платёж не найден", show_alert=True)
        return
    if payment["status"] != "pending":
        await cb.answer("Этот платёж уже обработан", show_alert=True)
        return

    await cb.message.edit_text(
        f"✅ <b>Заявка на пополнение отправлена!</b>\n\n"
        f"Сумма: <b>{fmt_price(payment['amount'])}</b>\n"
        f"⏳ Ожидайте подтверждения администратора.\n\n"
        f"🆔 Номер заявки: <code>{payment_id}</code>",
        parse_mode="HTML",
    )

    # Notify admins
    username = f"@{payment['username']}" if payment.get("username") else "нет username"
    admin_text = (
        f"💰 <b>Новая заявка на пополнение</b>\n\n"
        f"👤 Пользователь: {payment.get('full_name', 'Неизвестно')}\n"
        f"🔗 Username: {username}\n"
        f"🆔 Telegram ID: <code>{payment['telegram_id']}</code>\n"
        f"💵 Сумма: <b>{fmt_price(payment['amount'])}</b>\n"
        f"🆔 Платёж #: <code>{payment_id}</code>"
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                admin_text,
                reply_markup=admin_payment_kb(payment_id),
                parse_mode="HTML",
            )
        except Exception:
            pass
