from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import StateFilter

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import get_cancel_keyboard, get_main_keyboard, get_halloffame_keyboard
from keyboards import HallOfFamePaginationCallback

from database.models import User, UserStatus, Project, Category, SubCategory
from database.requests import get_hof_projects

from shared.db.hallfame_models import HallOfFame

import html

general_router = Router()

@general_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_session: AsyncSession, user: User):

    await state.clear()
        
    if user.status == UserStatus.NEW:
        await message.answer(f"С возвращением!", reply_markup=get_main_keyboard())

    else:
        await message.answer(f"С возвращением, {user.name}!", reply_markup=get_main_keyboard())


@general_router.message(StateFilter(None), F.text == "🏆 Зал славы")
async def cmd_hof(message: Message, state: FSMContext, db_session: AsyncSession):
    projects = await get_hof_projects(db_session)
        
    if not projects:
        await message.answer("🦗 <b>Зал славы пуст...</b>", show_alert=True)
        return
        
    current_index = 0
    current_project = projects[current_index]
    
    # 4. Формируем текст и клавиатуру с помощью наших функций из прошлого шага
    text = await format_hof_project_text(current_project, db_session, len(projects), current_index=current_index)
    keyboard = get_halloffame_keyboard(current_index, len(projects))
    
    # 5. Отправляем сообщение пользователю
    await message.answer(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def format_hof_project_text(hof: HallOfFame, db_session, total_count, current_index) -> str:

    TEXT = (
        f'🏛 <b>Зал славы: </b>{current_index + 1} из {total_count}\n\n'
        f'<b><a href="{html.escape(hof.project.link)}">{html.escape(hof.project.name)}</a></b> — {html.escape(hof.project.subtitle)}\n\n'
        f'🥇 <b>Автор: {html.escape(hof.project.user.name)}</b>\n'
        f'💬 <b>О себе: {html.escape(hof.project.user.about)}</b>\n'
        f'<b><a href="{html.escape(hof.project.user.portfolio)}">🔗 Найти автора можно здесь</a></b>\n'
    )

    return TEXT


@general_router.callback_query(HallOfFamePaginationCallback.filter())
async def process_pagination(callback: types.CallbackQuery, callback_data: HallOfFamePaginationCallback, db_session: AsyncSession):
    user_id = callback.from_user.id
    target_index = callback_data.index
    
    projects = await get_hof_projects(db_session)
    
    if not projects:
        await callback.answer("🦗 Зал славы пуст...", show_alert=True)
        return

    if target_index >= len(projects):
        target_index = 0
        
    current_project = projects[target_index]
    
    # 2. Формируем новый текст и клавиатуру
    text = await format_hof_project_text(current_project, db_session, len(projects), current_index=target_index)
    keyboard = get_halloffame_keyboard(target_index, len(projects))
    
    # 3. Обновляем сообщение (вместо отправки нового!)
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    await callback.answer() # Убираем часики с кнопки