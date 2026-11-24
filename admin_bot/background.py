import asyncio
import json

import redis.asyncio as aioredis

from aiogram import Bot

from shared.config import config

from messages import send_user_reg_approval_form, send_project_approval_form


async def start_moderation_worker(bot: Bot):
    redis_client = aioredis.from_url(f"redis://default:{config.redis_password.get_secret_value()}@redis:6379/0")
    ADMIN_CHAT_ID = config.superuser_tg_id
    
    print("🟢 Воркер модерации второго бота запущен...")

    while True:
        try:
            result = await redis_client.brpop("public_admin_moder_queue", timeout=0)
            if result:
                _, raw_data = result
                data = json.loads(raw_data.decode("utf-8"))

                _type = data["_type"]

                if _type == "registration":
                
                    user_id = data["user_id"]
                    name = data["name"]
                    portfolio = data["portfolio"]
                    about = data["about"]

                    await send_user_reg_approval_form(bot, ADMIN_CHAT_ID, user_id, name, portfolio, about)

                elif _type == "project_submit":

                    user_id = data["user_id"]
                    project_id = data["project_id"]
                    name = data["name"]
                    link = data["link"]
                    subtitle = data["subtitle"]
                    summ = data["summ"]
                    uniq = data["uniq"]
                    cat = data["cat"]
                    scat = data["scat"]

                    await send_project_approval_form(bot, ADMIN_CHAT_ID, user_id, project_id, 
                                               link, name, subtitle, summ, uniq, cat, scat
                                               )

        except Exception as e:
            print(f"Ошибка в воркере модерации: {e}")
            await asyncio.sleep(3)