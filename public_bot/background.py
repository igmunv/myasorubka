import asyncio
import json
import redis.asyncio as aioredis
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from database.base import async_session_maker
from database.models import User, Project, ProjectStatus, UserStatus
from config import config
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

import html
from datetime import datetime, timedelta

from sqlalchemy import select, func

from keyboards import get_main_keyboard

async def start_notification_worker(bot: Bot):
    redis_client = aioredis.from_url(f"redis://default:{config.redis_password.get_secret_value()}@redis:6379/0")
    print("🟢 Воркер уведомлений запущен...")

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

                    # Обновляем статус в базе данных
                    async with async_session_maker() as session:
                        user = await session.get(User, user_id)
                        if user:
                            user.status = UserStatus.READY if decision == "approved" else UserStatus.FAIL
                            await session.commit()

                    # Шлем сообщение пользователю
                    if decision == "approved":

                        await bot.send_message(user_id, "🛂 Фейс-контроль пройден!\n\nТеперь ты можешь отправлять свои проекты на мясорубку 📁🥩", reply_markup=get_main_keyboard())
                    else:
                        await bot.send_message(user_id, f"❌ К сожалению, фейс-контроль не пройден:\n\n<blockquote>{reason}</blockquote>\n\nПопробуй ещё раз отправив сюда /start", parse_mode="HTML")

                if _type == "project_submit":

                    user_id = data["user_id"]
                    decision = data["decision"]
                    reason = data["reason"]
                    project_id = data["project_id"]

                    async with async_session_maker() as session:
                        project = await session.get(Project, project_id)
                        if project:
                            if decision == "approved":
                                project.status = ProjectStatus.READY
                            else:
                                await session.delete(project)
                            await session.commit()

                    if decision == "approved":

                        # async with async_session_maker() as session:
                        #     queue_number = await get_project_queue_number(session, project_id)

                        # battle_date = get_battle_date(queue_number)
                        # formatted_date = battle_date.strftime("%d.%m.%Y")

                        # await bot.send_message(user_id, "✅ <b>Проект принят!</b>\n\n" \
                        #                     f"Порядковый номер в очереди: <b>№{queue_number}</b>\n" \
                        #                     f"ориентировочная дата батла: <b>{formatted_date} (ВСК)</b>",
                        #                     parse_mode="HTML",
                        #                     reply_markup=get_main_keyboard())

                        await bot.send_message(user_id, "✅ <b>Проект принят!</b>",
                                                parse_mode="HTML",
                                                reply_markup=get_main_keyboard())
                        
                    else:
                        await bot.send_message(user_id, f"❌ К сожалению, проект на мясорубку не принят:\n\n<blockquote>{html.escape(reason)}</blockquote>\n\nПопробуй отправить ещё раз", 
                                               parse_mode="HTML",
                                               reply_markup=get_main_keyboard())



                    
        except Exception as e:
            print(f"Ошибка в воркере уведомлений: {e}")
            await asyncio.sleep(3)
