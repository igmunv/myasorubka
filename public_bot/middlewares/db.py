from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import TelegramObject
from database.base import async_session_maker
from aiogram.types import TelegramObject, Message, User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, UserStatus
from keyboards import get_main_keyboard
import logging


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with async_session_maker() as session:
            data["db_session"] = session
            return await handler(event, data)


class RegisterUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        event_user: TelegramUser | None = data.get("event_from_user")
        db_session: AsyncSession | None = data.get("db_session")
        bot = data.get("bot")  # Получаем экземпляр бота из контекста aiogram

        if event_user and db_session:
            user = await db_session.get(User, event_user.id)
            if not user:
                # 1. Создаем нового пользователя в БД
                user = User(
                    id=event_user.id,
                    name=None,
                    portfolio=None,
                    about=None,
                    status=UserStatus.NEW
                )
                db_session.add(user)
                try:
                    await db_session.commit()
                except Exception:
                    await db_session.rollback()
                    raise

                message = getattr(event, "message", None)

                if isinstance(message, Message) and bot:

                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=(
                            "Привет! Я собираю проекты на еженедельную <b>мясорубку</b>🥩\n\n"
                            "А дальше всё решает комьюнити: люди в канале голосуют за лучший проект, и выигрывает реально сильнейший!\n\n"
                            "👇 Жми <b>«🚀 Отправить проект»</b>, чтобы ворваться в замес, посмотри самые крутые проекты в <b>«🏆 Зале славы»</b> "
                            "или загляни в свой <b>«👤 Профиль»</b>"
                        ),
                        parse_mode="HTML",  
                        reply_markup=get_main_keyboard()
                    )

                    return

            data["db_user"] = user

        return await handler(event, data)