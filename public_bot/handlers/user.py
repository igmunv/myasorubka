from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import get_cancel_keyboard, get_main_keyboard

from states import FaceControlState

from database.models import User

import redis.asyncio as aioredis

from config import config

user_router = Router()

@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_session: AsyncSession):

    await state.clear()

    user = await db_session.get(User, message.from_user.id)

    if not user:

        await message.answer(
            "Привет! Я собираю проекты на еженедельную <b>мясорубку</b>🥩\n\nА дальше всё решает комьюнити: люди в канале голосуют за лучший проект, и выигрывает реально сильнейший!",
            parse_mode="HTML"
            )
        
        await message.answer(
            "✋ <b>Но чтобы получить доступ к отправке проектов, пройди короткий фейс-контроль (регистрацию)</b>\n\nМы держим планку комьюнити, а если твой проект победит — <b>твоё портфолио уйдёт в отдельный рекламный пост на весь канал!</b>",
            parse_mode="HTML", 
            reply_markup=get_cancel_keyboard()
            )
        
        await state.set_state(FaceControlState.waiting_for_name)

        await message.answer(
            "1️⃣ <b>Твоё имя или никнейм:</b>",
            parse_mode="HTML"
            )
        
    else:

        if not user.is_verified and user.is_checked:
            await message.answer(
                "🔄 <b>Давай попробуем пройти фейс-контроль ещё раз</b>",
                parse_mode="HTML", 
                reply_markup=get_cancel_keyboard()
                )

            await state.set_state(FaceControlState.waiting_for_name)
            
            await message.answer(
                "1️⃣ <b>Твоё имя или никнейм:</b>",
                parse_mode="HTML"
                )
            
        elif user.is_verified:
            await message.answer(f"С возвращением, {user.name}!", reply_markup=get_main_keyboard())

        else:
            await message.answer(f"С возвращением, {user.name}! Ждём решения модераторов...")


