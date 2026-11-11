import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.client.session.aiohttp import AiohttpSession

from database.base import init_db, async_session_maker

from database.init_categories import sync_categories as sync_db_cats

from handlers.general import general_router
from handlers.registration import registration_router
from handlers.project_submit import project_submit_router

from middlewares.db import DbSessionMiddleware, RegisterUserMiddleware

from config import config

from background import start_notification_worker

async def main():

    logging.basicConfig(level=logging.INFO)

    await init_db()

    async with async_session_maker() as session:
        await sync_db_cats(session)
    
    storage = RedisStorage.from_url(
        f"redis://default:{config.redis_password.get_secret_value()}@redis:6379/0",
        key_builder=DefaultKeyBuilder(with_bot_id=True)
    )

    proxy_url = config.proxy_url.get_secret_value() if config.proxy_url else None

    session = AiohttpSession(proxy=proxy_url) if proxy_url else None
    bot = Bot(token=config.public_bot_token.get_secret_value(), session=session)
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(RegisterUserMiddleware())

    dp.include_router(registration_router)
    dp.include_router(project_submit_router)
    dp.include_router(general_router)

    asyncio.create_task(start_notification_worker(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
