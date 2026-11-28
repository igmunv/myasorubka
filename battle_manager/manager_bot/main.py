import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.client.session.aiohttp import AiohttpSession

from manager_bot.handlers.general import general_router
from manager_bot.middlewares.db import DbSessionMiddleware

from shared.config import config


async def main():

    logging.basicConfig(level=logging.INFO)
    
    storage = RedisStorage.from_url(
        f"redis://default:{config.redis_password.get_secret_value()}@redis:6379/0",
        key_builder=DefaultKeyBuilder(with_bot_id=True)
    )

    proxy_url = config.proxy_url.get_secret_value() if config.proxy_url else None

    session = AiohttpSession(proxy=proxy_url) if proxy_url else None
    bot = Bot(token=config.manager_bot_token.get_secret_value(), session=session)
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DbSessionMiddleware())

    dp.include_router(general_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
