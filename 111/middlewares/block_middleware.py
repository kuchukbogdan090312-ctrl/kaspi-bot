from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Any, Awaitable, Callable, Dict
from services.user_service import get_or_create_user, get_user


class BlockMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if user:
            db_user = await get_or_create_user(
                user.id,
                user.username,
                user.full_name,
            )
            data["db_user"] = db_user
            if db_user.get("is_blocked"):
                if isinstance(event, Message):
                    await event.answer("🚫 Вы заблокированы и не можете использовать бота.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("🚫 Вы заблокированы.", show_alert=True)
                return

        return await handler(event, data)
