from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import StateFilter

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import get_cancel_keyboard, get_main_keyboard

fallback_router = Router()

@fallback_router.callback_query()
async def unhandled_callbacks(callback: types.CallbackQuery):
    await callback.answer("Находится разработке 🚧", show_alert=True)