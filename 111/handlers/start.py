from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from keyboards.keyboards import main_menu_kb
from utils.helpers import fmt_price, fmt_date

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: dict):
    name = message.from_user.first_name or "друг"
    await message.answer(
        f"👋 Привет, <b>{name}</b>!\n\n"
        f"Добро пожаловать в бот подписки на закрытое сообщество.\n\n"
        f"Выберите раздел в меню ниже 👇",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )


@router.message(F.text == "👤 Профиль")
async def profile_handler(message: Message, db_user: dict):
    from services.subscription_service import get_user_subscriptions
    from utils.helpers import sub_status_text, is_sub_active

    subs = await get_user_subscriptions(message.from_user.id)
    active_count = sum(1 for s in subs if is_sub_active(s))

    text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"👤 Имя: {message.from_user.full_name}\n"
        f"💰 Баланс: <b>{fmt_price(db_user['balance'])}</b>\n"
        f"🎟 Активных подписок: <b>{active_count}</b>\n"
        f"📅 Дата регистрации: {fmt_date(db_user.get('created_at', ''))}"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "ℹ️ Поддержка")
async def support_handler(message: Message):
    await message.answer(
        "ℹ️ <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы — напишите нам:\n\n"
        "📧 Администратор: @admin течение 24 часов\n\n"
        "Укажите это сообщение при обращении иначе мы не примем запрос: Здраствуйте! у меня есть вопрос id "
        f"<code>{message.from_user.id}</code>",
        parse_mode="HTML",
    )
