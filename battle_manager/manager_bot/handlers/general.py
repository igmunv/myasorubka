from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Filter

from manager_bot.keyboards import get_main_keyboard

from shared.config import config

from sqlalchemy.ext.asyncio import AsyncSession

import battle

general_router = Router()

ADMIN_ID = config.superuser_tg_id

class IsAllowedUser(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == ADMIN_ID

general_router.message.filter(IsAllowedUser())


@general_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):

    await state.clear()
            
    await message.answer(f"С возвращением!", reply_markup=get_main_keyboard())


@general_router.message(F.text == "Новый Батл")
async def handle_users_button(message: Message, state: FSMContext, db_session: AsyncSession) -> None:
    await message.answer(f"Создаю...")

    btl_info = await battle.create(db_session)

    if not btl_info:
        await message.answer(f"Не получилось :(")

    new_battle = btl_info["battle"]
    projects = btl_info["projects"]

    battle_text = await battle.text_gen(new_battle, projects)
    await message.answer(battle_text, parse_mode="HTML", disable_web_page_preview=True)