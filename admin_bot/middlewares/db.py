from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import TelegramObject

from database.base import async_session_maker as admin_asm
from public_bot_db.base import async_session_maker as public_asm


class DBAdminSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with admin_asm() as session:
            data["db_session"] = session
            return await handler(event, data)

class DBPublicSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with public_asm() as session:
            data["db_public_session"] = session
            return await handler(event, data)