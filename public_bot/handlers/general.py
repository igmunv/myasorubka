from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import StateFilter

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import get_cancel_keyboard, get_main_keyboard

from database.models import User, UserStatus

import redis.asyncio as aioredis

from config import config

general_router = Router()

@general_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_session: AsyncSession):

    await state.clear()

    user = await db_session.get(User, message.from_user.id)
        
    if user.status == UserStatus.NEW:
        await message.answer(f"С возвращением!", reply_markup=get_main_keyboard())

    else:
        await message.answer(f"С возвращением, {user.name}!", reply_markup=get_main_keyboard())


@general_router.message(StateFilter(None), F.text == "👤 Профиль")
async def cmd_profile(message: Message, state: FSMContext, db_session: AsyncSession):
    user = await db_session.get(User, message.from_user.id)
    await message.answer(f"🔜 Скоро...")


@general_router.message(StateFilter(None), F.text == "🏆 Зал славы")
async def cmd_hof(message: Message, state: FSMContext, db_session: AsyncSession):
    user = await db_session.get(User, message.from_user.id)
    await message.answer(f"🔜 Скоро...")