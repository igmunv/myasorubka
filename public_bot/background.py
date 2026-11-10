import asyncio
import json
import redis.asyncio as aioredis
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from database.base import async_session_maker
from database.models import User, Project, ProjectStatus
from config import config
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

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
                            user.is_verified = True if decision == "approved" else False
                            user.is_checked = True
                            await session.commit()

                    # Шлем сообщение пользователю
                    if decision == "approved":

                        await bot.send_message(user_id, "🛂 Фейс-контроль пройден!\n\nТеперь ты можешь отправлять свои проекты на мясорубку 📁🥩", reply_markup=get_main_keyboard())
                    else:
                        await bot.send_message(user_id, f"❌ К сожалению, фейс-контроль не пройден:\n\n<blockquote>{reason}</blockquote>\n\nПопробуй ещё раз отправив сюда /start", parse_mode="HTML")

                if _type == "project_submit":

                    print("project_submit")

                    user_id = data["user_id"]
                    decision = data["decision"]
                    reason = data["reason"]
                    project_id = data["project_id"]

                    async with async_session_maker() as session:
                        print("await session.get(Project, project_id)")
                        project = await session.get(Project, project_id)
                        if project:

                            print("if project")

                            if decision == "approved":
                                print("approved")
                                project.status = ProjectStatus.READY if decision == "approved" else ProjectStatus.FAIL
                                await session.commit()

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
                        await bot.send_message(user_id, f"❌ К сожалению, проект на мясорубку не принят:\n\n<blockquote>{reason}</blockquote>\n\nПопробуй отправить ещё раз", 
                                               parse_mode="HTML",
                                               reply_markup=get_main_keyboard())



                    
        except Exception as e:
            print(f"Ошибка в воркере уведомлений: {e}")
            await asyncio.sleep(3)


def get_battle_date(queue_number: int) -> datetime:
    today = datetime.now()
    
    # 1. Считаем, сколько полных батлов перед этим проектом (0 - текущий, 1 - следующий и т.д.)
    # Если queue_number от 1 до 3, то weeks_offset = 0
    weeks_offset = max(0, (queue_number - 1) // 3)
    
    # 2. Ищем ближайшее воскресенье (в Python понедельник = 0, воскресенье = 6)
    days_until_sunday = (6 - today.weekday()) % 7
    
    # Если сегодня воскресенье, но батл уже идет/прошел, можно решить, считать ли сегодня за день батла. 
    # Обычно если сегодня ВСК, то проекты текущего батла уже стартовали.
    if days_until_sunday == 0 and today.hour >= 12:  # например, после старта в 12:00
        # Если сегодня уже воскресенье вечер, то "следующее воскресенье" для текущей тройки — это сегодня, 
        # но для #4 это уже след. воскресенье. 
        pass

    next_sunday = today + timedelta(days=days_until_sunday)
    
    # Сбрасываем время на 12:00 (время старта батла)
    next_sunday = next_sunday.replace(hour=12, minute=0, second=0, microsecond=0)
    
    # Если сегодня воскресенье, но до 12:00, то ближайшее воскресенье — это сегодня. 
    # Если после 12:00, то для тех, кто попал в текущий батл (weeks_offset == 0), это «сегодня/уже идет», 
    # а для остальных — считаем от следующей недели.
    if days_until_sunday == 0 and today.hour < 12:
        target_date = next_sunday + timedelta(weeks=weeks_offset)
    else:
        # Если сегодня не воскресенье, считаем от ближайшего воскресенья
        target_date = next_sunday + timedelta(weeks=weeks_offset)
        
    return target_date


async def get_project_queue_number(session, target_project_id: int) -> int | None:
    subq = (
        select(
            Project.id,
            func.row_number()
            .over(order_by=Project.created_at.asc())  
            .label("queue_number")
        )
        .where(Project.is_verified == True)  
        .subquery()
    )

    stmt = select(subq.c.queue_number).where(subq.c.id == target_project_id)
    
    result = await session.execute(stmt)
    return result.scalar_one_or_none()