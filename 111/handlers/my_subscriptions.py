from aiogram import Router, F
from aiogram.types import Message
from services.subscription_service import get_user_subscriptions, deactivate_expired
from services.payment_service import get_setting
from keyboards.keyboards import community_kb, main_menu_kb
from utils.helpers import fmt_date, is_sub_active, sub_status_text

router = Router()


@router.message(F.text == "🛒 Мои подписки")
async def my_subscriptions(message: Message):
    await deactivate_expired()
    subs = await get_user_subscriptions(message.from_user.id)
    if not subs:
        await message.answer(
            "📭 У вас пока нет подписок.\n\n"
            "Перейдите в раздел «📚 Подписки», чтобы оформить доступ.",
        )
        return

    community_link = await get_setting("community_link") or "#"
    community_name = await get_setting("community_name") or "сообщество"

    active_subs = [s for s in subs if is_sub_active(s)]
    expired_subs = [s for s in subs if not is_sub_active(s)]

    lines = ["🛒 <b>Мои подписки</b>\n"]

    if active_subs:
        lines.append("✅ <b>Активные:</b>")
        for sub in active_subs:
            expires = "Навсегда ♾️" if not sub.get("expires_at") else fmt_date(sub["expires_at"])
            lines.append(f"  {sub['emoji']} {sub['plan_name']} — до {expires}")
        lines.append("")

    if expired_subs:
        lines.append("❌ <b>Истёкшие:</b>")
        for sub in expired_subs[:3]:
            expires = fmt_date(sub.get("expires_at", ""))
            lines.append(f"  {sub['emoji']} {sub['plan_name']} — истекла {expires}")

    text = "\n".join(lines)

    if active_subs:
        await message.answer(
            text,
            reply_markup=community_kb(community_link),
            parse_mode="HTML",
        )
    else:
        await message.answer(text, parse_mode="HTML")
