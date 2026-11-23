from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

general_router = Router()

@general_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):

    await state.clear()
        
    await message.answer(f"es")