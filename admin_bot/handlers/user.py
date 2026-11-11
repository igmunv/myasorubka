from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, CallbackQuery

from typing import Callable, Dict, Any, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import asyncio
import redis.asyncio as aioredis
import json

from states import RegRejectedState, ProjSubmitRejectState

from config import config

from public_bot_db.models import User

admin_router = Router()


ALLOWED_USER_IDS = [config.superuser_tg_id]

redis_client = aioredis.from_url(f"redis://default:{config.redis_password.get_secret_value()}@redis:6379/0")

@admin_router.message.outer_middleware
async def check_user_id_middleware(
    handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
    event: Message,
    data: Dict[str, Any]
) -> Any:

    if event.from_user.id not in ALLOWED_USER_IDS:
        return
    
    return await handler(event, data)


@admin_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_mmyaso_session: AsyncSession, db_submeat_session: AsyncSession):

    user_count = await db_submeat_session.scalar(
        select(func.count()).select_from(User)
    )

    await message.answer(f"💚 Я жив\n\nКоличество пользователей: {user_count}")


@admin_router.callback_query(F.data.startswith("mod_registration_"))
async def process_reg_moderation_callback(callback: CallbackQuery, state: FSMContext):
    action, user_id_str = callback.data.split(":")
    user_id = int(user_id_str)
    
    decision = "approved" if action == "mod_registration_approve" else "rejected"

    if decision == "approved":
    
        payload = json.dumps({
            "_type": "registration",
            "user_id": user_id,
            "decision": decision,
            "reason": ""
        })
        await redis_client.lpush("admin_public_moder_queue", payload)

        status_text = "✅ Одобрено" if decision == "approved" else "❌ Отклонено"
        await callback.message.edit_text(f"{callback.message.text}\n\n<b>Статус: {status_text}</b>", parse_mode="HTML")
        await callback.answer("Решение отправлено!")

    elif decision == "rejected":

        chat_id = callback.message.chat.id
        message_id = callback.message.message_id
        
        await state.set_state(RegRejectedState.waiting_for_reason)
        await state.update_data(user_id=user_id, chat_id=chat_id, msg_id=message_id, msg_text=callback.message.text) 

        await callback.message.answer("📝 <b>Напиши причину:</b>", parse_mode="HTML")


@admin_router.message(RegRejectedState.waiting_for_reason)
async def process_reg_reason(message: Message, state: FSMContext):

    if message.text:

        reason = message.text.strip()

        if len(reason) < 3:
            await message.answer("❗️ <b>Слишком коротко (минимум 3 символа)</b>", parse_mode="HTML")

        else:

            user_data = await state.get_data()
            user_id = user_data["user_id"]
            chat_id = user_data["chat_id"]
            msg_id = user_data["msg_id"]
            msg_text = user_data["msg_text"]

            payload = json.dumps({
                "_type": "registration",
                "user_id": user_id,
                "decision": "rejected",
                "reason": reason
            })
            await redis_client.lpush("admin_public_moder_queue", payload)

            await message.bot.edit_message_text(
                text=f"{msg_text}\n\n<b>Статус: ❌ Отклонено</b>",
                chat_id=chat_id,
                message_id=msg_id,
                reply_markup=None, 
                parse_mode="HTML"
            )
            await message.answer("✅ <b>Принято</b>", parse_mode="HTML")

            await state.clear()


@admin_router.callback_query(F.data.startswith("mod_project_submit_"))
async def process_projsub_moderation_callback(callback: CallbackQuery, state: FSMContext):
    action, user_id_str, project_id_str = callback.data.split(":")
    user_id = int(user_id_str)
    project_id = int(project_id_str)
    
    decision = "approved" if action == "mod_project_submit_approve" else "rejected"

    if decision == "approved":

        payload = json.dumps({
            "_type": "project_submit",
            "user_id": user_id,
            "project_id": project_id,
            "decision": decision,
            "reason": ""
        })
        await redis_client.lpush("admin_public_moder_queue", payload)

        status_text = "✅ Одобрено" if decision == "approved" else "❌ Отклонено"
        await callback.message.edit_text(f"{callback.message.text}\n\n<b>Статус: {status_text}</b>", parse_mode="HTML")
        await callback.answer("Решение отправлено!")

    elif decision == "rejected":

        chat_id = callback.message.chat.id
        message_id = callback.message.message_id
        
        await state.set_state(ProjSubmitRejectState.waiting_for_reason)
        await state.update_data(user_id=user_id, chat_id=chat_id, msg_id=message_id, msg_text=callback.message.text, project_id=project_id) 

        await callback.message.answer("📝 <b>Напиши причину:</b>", parse_mode="HTML")


@admin_router.message(ProjSubmitRejectState.waiting_for_reason)
async def process_projsub_reason(message: Message, state: FSMContext):

    if message.text:

        reason = message.text.strip()

        if len(reason) < 3:
            await message.answer("❗️ <b>Слишком коротко (минимум 3 символа)</b>", parse_mode="HTML")

        else:

            user_data = await state.get_data()
            user_id = user_data["user_id"]
            chat_id = user_data["chat_id"]
            msg_id = user_data["msg_id"]
            msg_text = user_data["msg_text"]
            project_id = user_data["project_id"]

            payload = json.dumps({
                "_type": "project_submit",
                "user_id": user_id,
                "project_id": project_id,
                "decision": "rejected",
                "reason": reason
            })
            await redis_client.lpush("admin_public_moder_queue", payload)

            await message.bot.edit_message_text(
                text=f"{msg_text}\n\n<b>Статус: ❌ Отклонено</b>",
                chat_id=chat_id,
                message_id=msg_id,
                reply_markup=None, 
                parse_mode="HTML", 
                disable_web_page_preview=True
            )
            await message.answer("✅ <b>Принято</b>", parse_mode="HTML")

            await state.clear()