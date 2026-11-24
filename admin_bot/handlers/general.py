from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import config

from keyboards import get_main_sponsr_keyboard, get_main_admin_keyboard
from aiogram.filters import Filter

general_router = Router()

ALLOWED_USER_IDS = [config.superuser_tg_id, config.secret_spons_tg_id]


class IsAllowedUser(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ALLOWED_USER_IDS

general_router.message.filter(IsAllowedUser())

@general_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_session: AsyncSession):
    if message.from_user.id == config.superuser_tg_id:
        await message.answer(f"💚 Я жив", reply_markup=get_main_admin_keyboard())

    else:
        await message.answer(f"💚 Я жив", reply_markup=get_main_sponsr_keyboard())