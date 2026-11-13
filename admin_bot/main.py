import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.client.session.aiohttp import AiohttpSession

from handlers.user import admin_router
from handlers.projects import projects_router
from handlers.general import general_router

from middlewares.db import DBAdminSessionMiddleware, DBPublicSessionMiddleware

from config import config

from background import start_moderation_worker

from database.base import init_db

async def main():

    logging.basicConfig(level=logging.INFO)

    await init_db()
    
    storage = RedisStorage.from_url(
        f"redis://default:{config.redis_password.get_secret_value()}@redis:6379/0",
        key_builder=DefaultKeyBuilder(with_bot_id=True)
    )

    proxy_url = config.proxy_url.get_secret_value() if config.proxy_url else None
    
    session = AiohttpSession(proxy=proxy_url) if proxy_url else None
    bot = Bot(token=config.admin_bot_token.get_secret_value(), session=session)
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DBAdminSessionMiddleware())
    dp.update.middleware(DBPublicSessionMiddleware())

    dp.include_router(admin_router)
    dp.include_router(projects_router)
    dp.include_router(general_router)

    asyncio.create_task(start_moderation_worker(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
