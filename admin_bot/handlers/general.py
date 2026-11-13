from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession

from config import config

from keyboards import get_main_sponsr_keyboard
from aiogram.filters import Filter

general_router = Router()

ALLOWED_USER_IDS = [config.superuser_tg_id, config.secret_spons_tg_id]


class IsAllowedUser(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ALLOWED_USER_IDS

general_router.message.filter(IsAllowedUser())

@general_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_session: AsyncSession, db_public_session: AsyncSession):
    await message.answer(f"💚 Я жив", reply_markup=get_main_sponsr_keyboard())