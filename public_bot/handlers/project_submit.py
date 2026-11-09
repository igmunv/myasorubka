from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import StateFilter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from states import ProjectSubmitState

from database.models import User, Project

import redis.asyncio as aioredis

from config import config

import validators
import json

from keyboards import CategoryPagination, CategorySelect, get_cancel_keyboard, get_categories_keyboard


project_submit_router = Router()

redis_client = aioredis.from_url(f"redis://default:{config.redis_password.get_secret_value()}@redis:6379/0")


ITEMS_PER_PAGE = 5

FAKE_DB_CATEGORIES = [{"id": i, "name": f"📁 Категория {i}"} for i in range(1, 18)]


async def get_user_project(session: AsyncSession, user_id: int) -> Project | None:
    """Возвращает проект пользователя или None, если проекта нет."""
    stmt = select(Project).where(
        Project.user_id == user_id,
        # Если проект может быть удален/отклонен,
        # раскомментируй проверку активного статуса:
        # Project.status.in_(["draft", "moderation", "in_queue"])
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


@project_submit_router.message(ProjectSubmitState(), F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🙅‍♂️ <b>Отправка проекта отменена</b>", 
                        parse_mode="HTML",
                        reply_markup=ReplyKeyboardRemove())


@project_submit_router.message(StateFilter(None), F.text == "📁 Отправить проект")
async def cmd_send_project(message: Message, state: FSMContext, db_session: AsyncSession):
    user = await db_session.get(User, message.from_user.id)
    
    if user and user.is_verified:

        # проверка на то что чел уже скинул проект
        project = await get_user_project(db_session, user_id=message.from_user.id)

        if project:
            await message.answer("⚠️ <b>Твой проект уже в очереди!</b>\n\nНаберись терпения - скоро он отправится на Мясорубку 🕘",
                                parse_mode="HTML")

        else:
            await state.set_state(ProjectSubmitState.waiting_for_general_category)
            await message.answer("<b>Отлично! Начинаем заполнять твою заявку на мясорубку!</b> 🔥\n\n" \
                                "<b>❗️Внимание: эти данные улетят в общий пост на канале</b>, поэтому заполняй все без ошибок и так, чтобы народ реально хотел за тебя проголосовать", 
                                parse_mode="HTML", 
                                reply_markup=get_cancel_keyboard())

            categories = FAKE_DB_CATEGORIES
            
            keyboard = get_categories_keyboard(
                categories=categories, page=0, items_per_page=ITEMS_PER_PAGE
            )
            
            await message.answer("1️⃣ <b>Выберите категорию:</b>", reply_markup=keyboard, parse_mode="HTML")
            
    else:
        await message.answer("✋ <b>Сначала нужно пройти фейс-контроль!</b>\n\nДля этого нажми /start", parse_mode="HTML")


# 2. Обработка переключения страниц (пагинация)
@project_submit_router.callback_query(CategoryPagination.filter())
async def process_category_pagination(
    callback: types.CallbackQuery, callback_data: CategoryPagination
):
    categories = FAKE_DB_CATEGORIES
    target_page = callback_data.page

    keyboard = get_categories_keyboard(
        categories=categories, page=target_page, items_per_page=ITEMS_PER_PAGE
    )

    # Обновляем клавиатуру у существующего сообщения
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


# 3. Заглушка для неактивных кнопок (например, счетчика страниц)
@project_submit_router.callback_query(F.data == "noop")
async def process_noop(callback: types.CallbackQuery):
    await callback.answer()


# 4. Обработка клика по конкретной категории
@project_submit_router.callback_query(CategorySelect.filter())
async def process_category_select(
    callback: types.CallbackQuery, callback_data: CategorySelect
):
    category_id = callback_data.id
    await callback.answer(
        f"Вы выбрали категорию с ID: {category_id}", show_alert=True
    )


@project_submit_router.message(ProjectSubmitState.waiting_for_general_category)
async def process_general_category(message: Message, state: FSMContext):

    if message.text:

        name = message.text.strip()

        if len(name) > 32:
            await message.answer("❗️ <b>Название слишком длинное (максимум 32 символа)</b>\n\nПопробуй ввести ещё раз:",
                                parse_mode="HTML")
        elif len(name) < 3:
            await message.answer("❗️ <b>Название слишком короткое (минимум 3 символа)</b>\n\nПопробуй ввести ещё раз:",
                                parse_mode="HTML")
        else:
            await state.update_data(name=name)
            await state.set_state(ProjectSubmitState.waiting_for_link)
            await message.answer("2️⃣ <b>Ссылка на проект (репозиторий, сайт):</b>",
                                parse_mode="HTML")

    else:
        await message.answer("❗️ <b>Не увидел название</b>\n\nПопробуй ввести ещё раз:",
                            parse_mode="HTML")


@project_submit_router.message(ProjectSubmitState.waiting_for_link)
async def process_link(message: Message, state: FSMContext):

    if message.text:
    
        link = message.text.strip()
    
        if validators.url(link):
            await state.update_data(link=link)
            await state.set_state(ProjectSubmitState.waiting_for_desc)
            await message.answer("3️⃣ <b>Короткое описание проекта (какую боль решает, фичи, стек):</b>",
                                parse_mode="HTML")

        else:
            await message.answer("❗️ <b>Это не ссылка</b>\n\nПопробуй ещё раз:",
                                parse_mode="HTML")


@project_submit_router.message(ProjectSubmitState.waiting_for_summary)
async def process_desc(message: Message, state: FSMContext, db_session: AsyncSession):

    if message.text:

        desc = message.text.strip()

        if len(desc) > 250:
            await message.answer("❗️ <b>Слишком много текста (максимум 250 символов)</b>\n\n" \
                                "Постарайся уложиться в короткое и емкое описание — именно его увидят подписчики" \
                                "Попробуй ещё раз:",
                                parse_mode="HTML")
        elif len(desc) < 15:
            await message.answer("❗️ <b>Слишком коротко (минимум 15 символов)</b>\n\n" \
                                "Расскажи о проекте чуть подробнее. Не забывай: именно это описание увидят подписчики\n\n" \
                                "Попробуй ещё раз:",
                                parse_mode="HTML")
        else:
            user_data = await state.get_data()
            name = user_data["name"]
            link = user_data["link"]

            await state.clear()

            project = Project(
                name=name,
                link=link,
                desc=desc,
                user_id=message.from_user.id
            )
            db_session.add(project)

            await db_session.commit()

            await db_session.refresh(project)

            project_id = project.id
            
            payload = json.dumps({
                "_type": "project_submit",
                "user_id": message.from_user.id,
                "username": message.from_user.username,
                "project_id": project_id,
                "name": name,
                "link": link,
                "desc": desc
            })
            await redis_client.lpush("moderation_queue", payload)

            await message.answer("⏳ <b>Проект и заявка отправлены на модерацию</b>\n\n",
                                parse_mode="HTML",
                                reply_markup=ReplyKeyboardRemove())
            