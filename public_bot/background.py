import asyncio
import json
import html
from datetime import datetime, timedelta

import redis.asyncio as aioredis

from aiogram import Bot

from keyboards import get_retry_registration_keyboard, get_fix_project_button, get_my_projects_button
from shared.config import config

async def start_notification_worker(bot: Bot):
    
    redis_client = aioredis.from_url(f"redis://default:{config.redis_password.get_secret_value()}@redis:6379/0")

    while True:
        try:
            result = await redis_client.brpop("admin_public_moder_queue", timeout=0)
            if result:
                _, raw_data = result
                data = json.loads(raw_data.decode("utf-8"))

                _type = data["_type"]

                if _type == "registration":
                
                    user_id = data["user_id"]
                    decision = data["decision"]
                    reason = data["reason"]

                    # Шлем сообщение пользователю
                    if decision == "approved":
                        await bot.send_message(user_id, "🛂 Фейс-контроль пройден!\n\nТеперь ты можешь отправлять свои проекты на мясорубку 📁🥩")
                    else:
                        await bot.send_message(user_id, f"❌ К сожалению, фейс-контроль не пройден:\n\n<blockquote>{reason}</blockquote>\n\n"
                                               "Поправь это и попробуй ещё раз 👇", 
                                               parse_mode="HTML",
                                               reply_markup=get_retry_registration_keyboard())

                if _type == "project_submit":

                    user_id = data["user_id"]
                    decision = data["decision"]
                    reason = data["reason"]
                    project_name = data["project_name"]
                    project_link = data["project_link"]
                    project_id = data["project_id"]
                    

                    project_info = f'<a href="{html.escape(project_link)}">{html.escape(project_name)}</a>'

                    if decision == "approved":
                        await bot.send_message(user_id, f"✅ <b>Проект {project_info} принят!</b>",
                                                parse_mode="HTML", 
                                                reply_markup=get_my_projects_button(),
                                               disable_web_page_preview=True)
                        
                    else:
                        await bot.send_message(user_id, f"❌ <b>К сожалению, проект {project_info} не прошёл модерацию</b>:\n\n"
                                               f"<blockquote>{html.escape(reason)}</blockquote>\n\n"
                                               "Исправь причину отказа и попробуй ещё раз 👇",
                                               parse_mode="HTML",
                                               reply_markup=get_fix_project_button(project_id=project_id),
                                               disable_web_page_preview=True)
                    
        except Exception as e:
            print(f"Ошибка в воркере уведомлений: {e}")
            await asyncio.sleep(3)
