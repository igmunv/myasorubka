from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import StateFilter
import html

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from states import ProjectSubmitState

from database.models import User, Project, Category, SubCategory, ProjectStatus, UserStatus
from database.requests import get_user_project, get_all_categories, get_subcategories_by_category

import redis.asyncio as aioredis

from config import config

import validators
import json

from keyboards import CategoryPagination, SubCategoryPagination, CategorySelect, SubCategorySelect
from keyboards import get_cancel_keyboard, get_categories_keyboard, get_yes_no_keyboard, get_main_keyboard, get_go_keyboard


project_submit_router = Router()

redis_client = aioredis.from_url(f"redis://default:{config.redis_password.get_secret_value()}@redis:6379/0")

MAX_PROJ_NAME_SIZE = 20
MAX_PROJ_SUBTITLE_SIZE = 50
MAX_PROJ_SUMM_SIZE = 120
MAX_PROJ_UNIQ_SIZE = 120

ITEMS_PER_PAGE = 4


@project_submit_router.message(ProjectSubmitState(), F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🙅‍♂️ <b>Отправка проекта отменена</b>", 
                        parse_mode="HTML",
                        reply_markup=get_main_keyboard())


@project_submit_router.message(StateFilter(None), F.text == "📁 Отправить проект")
async def cmd_send_project(message: Message, state: FSMContext, db_session: AsyncSession):
    user = await db_session.get(User, message.from_user.id)
    
    if user and user.status == UserStatus.READY:

        # проверка на то что чел уже скинул проект
        project = await get_user_project(db_session, user_id=message.from_user.id)

        if project:

            if project.status == ProjectStatus.READY:
                await message.answer("🕘 <b>Твой проект уже в очереди!</b>\n\nНаберись терпения - скоро он отправится на Мясорубку",
                                    parse_mode="HTML")

            elif project.status == ProjectStatus.WAIT:
                await message.answer("⛔️ <b>Твой проект на модерации!</b>",
                                    parse_mode="HTML")

        else:
            await state.set_state(ProjectSubmitState.waiting_for_start)
            await message.answer("<b>Отлично! Начинаем заполнять твою заявку на мясорубку!</b> 🔥",
                                parse_mode="HTML", 
                                reply_markup=get_cancel_keyboard())

            await message.answer("<b>❗️Внимание: эти данные улетят в общий пост на канале</b>, поэтому заполняй всё без ошибок и так, чтобы народ реально хотел за тебя проголосовать", 
                                parse_mode="HTML", 
                                reply_markup=get_go_keyboard())
            
    else:
        await message.answer("✋ <b>Сначала нужно пройти фейс-контроль!</b>\n\nДля этого нажми /start", parse_mode="HTML")


@project_submit_router.callback_query(ProjectSubmitState.waiting_for_start, F.data == "go")
async def process_go(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession):
    await state.set_state(ProjectSubmitState.waiting_for_category)

    categories = await get_all_categories(session=db_session);
                
    keyboard = get_categories_keyboard(
        categories=categories, page=0, items_per_page=ITEMS_PER_PAGE
    )
    
    await callback.message.answer("1️⃣ <b>Выбери категорию:</b>", reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# 2. Обработка переключения страниц (пагинация)
@project_submit_router.callback_query(CategoryPagination.filter(), ProjectSubmitState.waiting_for_category)
async def process_category_pagination(
    callback: types.CallbackQuery, callback_data: CategoryPagination, db_session: AsyncSession
):
    categories = await get_all_categories(session=db_session);
    target_page = callback_data.page

    keyboard = get_categories_keyboard(
        categories=categories, page=target_page, items_per_page=ITEMS_PER_PAGE
    )

    # Обновляем клавиатуру у существующего сообщения
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


# 2. Обработка переключения страниц (пагинация)
@project_submit_router.callback_query(SubCategoryPagination.filter(), ProjectSubmitState.waiting_for_sub_category)
async def process_sub_category_pagination(
    callback: types.CallbackQuery, callback_data: SubCategoryPagination, db_session: AsyncSession, state: FSMContext
):

    user_data = await state.get_data()
    category_id = user_data['category_id']
    
    subcategories = await get_subcategories_by_category(category_id=category_id, session=db_session);
    target_page = callback_data.page

    keyboard = get_categories_keyboard(
        categories=subcategories, page=target_page, items_per_page=ITEMS_PER_PAGE, is_subcat=True
    )

    # Обновляем клавиатуру у существующего сообщения
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


# 3. Заглушка для неактивных кнопок (например, счетчика страниц)
@project_submit_router.callback_query(F.data == "noop")
async def process_noop(callback: types.CallbackQuery):
    await callback.answer()


@project_submit_router.callback_query(
    StateFilter(
    ProjectSubmitState.waiting_for_category, 
    ProjectSubmitState.waiting_for_sub_category
    ), 
    F.data == "no_category_chosen")
async def process_no_category(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.delete()
    await callback.message.answer(
        "Выбран вариант «Нет подходящей категории». Можешь отправить запрос на добавление новой категории ему: @igmunv", reply_markup=get_main_keyboard()
    )
    await callback.answer()


# 4. Обработка клика по конкретной категории
@project_submit_router.callback_query(ProjectSubmitState.waiting_for_category, CategorySelect.filter())
async def process_category_select(
    callback: types.CallbackQuery, callback_data: CategorySelect, db_session: AsyncSession, state: FSMContext
):
    category_id = callback_data.id
    category = await db_session.get(Category, category_id)

    await state.update_data(category_id=category_id, category_name=category.name)
    await state.set_state(ProjectSubmitState.waiting_for_category_confirm)

    await callback.message.edit_text(f'🤔 <b>Выбрана категория "{category.name}"</b>:\n\n{category.desc}\n\n<b>Всё верно?</b>', 
                         reply_markup=get_yes_no_keyboard(), parse_mode="HTML")
    await callback.answer()

@project_submit_router.callback_query(ProjectSubmitState.waiting_for_category_confirm, F.data == "confirm_yes")
async def process_yes_category_confirm(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession):

    user_data = await state.get_data()
    category_name = user_data['category_name']
    category_id = user_data['category_id']

    await callback.message.edit_text(f'✅ <b>Выбрана категория "{category_name}"</b>', 
                                    parse_mode="HTML")
    await callback.answer()

    await state.set_state(ProjectSubmitState.waiting_for_sub_category)

    subcategories = await get_subcategories_by_category(category_id=category_id, session=db_session);
    
    keyboard = get_categories_keyboard(
        categories=subcategories, page=0, items_per_page=ITEMS_PER_PAGE, is_subcat=True
    )
    
    await callback.message.answer("2️⃣ <b>Выбери подкатегорию:</b>", reply_markup=keyboard, parse_mode="HTML")


@project_submit_router.callback_query(ProjectSubmitState.waiting_for_category_confirm, F.data == "confirm_no")
async def process_no_category_confirm(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession):

    await state.set_state(ProjectSubmitState.waiting_for_category)

    categories = await get_all_categories(session=db_session);
                
    keyboard = get_categories_keyboard(
        categories=categories, page=0, items_per_page=ITEMS_PER_PAGE
    )
            
    await callback.message.edit_text("🔁 <b>Выбери категорию еще раз:</b>", reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@project_submit_router.callback_query(ProjectSubmitState.waiting_for_sub_category, SubCategorySelect.filter())
async def process_sub_category_select(
    callback: types.CallbackQuery, callback_data: SubCategorySelect, db_session: AsyncSession, state: FSMContext
):
    sub_category_id = callback_data.id
    sub_category = await db_session.get(SubCategory, sub_category_id)

    await state.update_data(sub_category_id=sub_category_id, sub_category_name=sub_category.name)
    await state.set_state(ProjectSubmitState.waiting_for_sub_category_confirm)

    await callback.message.edit_text(f'🤔 <b>Выбрана подкатегория "{sub_category.name}"</b>:\n\n{sub_category.desc}\n\n<b>Всё верно?</b>', 
                         reply_markup=get_yes_no_keyboard(), parse_mode="HTML")
    await callback.answer()


@project_submit_router.callback_query(ProjectSubmitState.waiting_for_sub_category_confirm, F.data == "confirm_yes")
async def process_yes_sub_category_confirm(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession):

    user_data = await state.get_data()
    sub_category_name = user_data['sub_category_name']

    await callback.message.edit_text(f'✅ <b>Выбрана подкатегория "{sub_category_name}"</b>', 
                                    parse_mode="HTML")
    await callback.answer()

    await state.set_state(ProjectSubmitState.waiting_for_name)

    await callback.message.answer("3️⃣ <b>Название проекта:</b>",
                                parse_mode="HTML", reply_markup=get_cancel_keyboard())


@project_submit_router.callback_query(ProjectSubmitState.waiting_for_sub_category_confirm, F.data == "confirm_no")
async def process_no_sub_category_confirm(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession):

    user_data = await state.get_data()
    category_id = user_data['category_id']

    await state.set_state(ProjectSubmitState.waiting_for_sub_category)
    
    subcategories = await get_subcategories_by_category(category_id=category_id, session=db_session);
        
    keyboard = get_categories_keyboard(
        categories=subcategories, page=0, items_per_page=ITEMS_PER_PAGE, is_subcat=True
    )
            
    await callback.message.edit_text("🔁 <b>Выбери подкатегорию еще раз:</b>", reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
    



@project_submit_router.message(ProjectSubmitState.waiting_for_name)
async def process_name(message: Message, state: FSMContext):

    if message.text:

        name = message.text.strip()

        if len(name) > MAX_PROJ_NAME_SIZE:
            await message.answer(f"❗️ <b>Название слишком длинное (максимум {MAX_PROJ_NAME_SIZE} симв.)</b>\n\nПопробуй ввести ещё раз:",
                                parse_mode="HTML")
        elif len(name) < 3:
            await message.answer("❗️ <b>Название слишком короткое (минимум 3 символа)</b>\n\nПопробуй ввести ещё раз:",
                                parse_mode="HTML")
        else:
            await state.update_data(name=name)
            await state.set_state(ProjectSubmitState.waiting_for_link)
            await message.answer("4️⃣ <b>Ссылка на проект (репозиторий, сайт):</b>",
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
            await state.set_state(ProjectSubmitState.waiting_for_subtitle)
            await message.answer('5️⃣ <b>Подзаголовок (пример: "монолитное ядро", "мессенджер с ИИ"):</b>',
                                parse_mode="HTML")

        else:
            await message.answer("❗️ <b>Это не ссылка</b>\n\nПопробуй ещё раз:",
                                parse_mode="HTML")


@project_submit_router.message(ProjectSubmitState.waiting_for_subtitle)
async def process_subtitle(message: Message, state: FSMContext):
    if message.text:
    
        subtitle = message.text.strip()

        if len(subtitle) > MAX_PROJ_SUBTITLE_SIZE:
            await message.answer(f"❗️ <b>Подзаголовок слишком длинный (максимум {MAX_PROJ_SUBTITLE_SIZE} симв.)</b>\n\nПопробуй ввести ещё раз:",
                                parse_mode="HTML")
        elif len(subtitle) < 5:
            await message.answer("❗️ <b>Подзаголовок слишком короткий (минимум 5 символов)</b>\n\nПопробуй ввести ещё раз:",
                                parse_mode="HTML")
        else:
            await state.update_data(subtitle=subtitle)
            await state.set_state(ProjectSubmitState.waiting_for_summary)
            await message.answer("6️⃣ <b>В чем суть проекта:</b>",
                                    parse_mode="HTML")
            
    else:
        await message.answer("❗️ <b>Не увидел подзаголовок</b>\n\nПопробуй ввести ещё раз:",
                            parse_mode="HTML")


@project_submit_router.message(ProjectSubmitState.waiting_for_summary)
async def process_summary(message: Message, state: FSMContext, db_session: AsyncSession):

    if message.text:

        summary = message.text.strip()

        if len(summary) > MAX_PROJ_SUMM_SIZE:
            await message.answer(f"❗️ <b>Слишком много текста (максимум {MAX_PROJ_SUMM_SIZE} симв.)</b>\n\n" \
                                "Постарайся уложиться в короткое и емкое описание — его увидят подписчики" \
                                "Попробуй ещё раз:",
                                parse_mode="HTML")
        elif len(summary) < 15:
            await message.answer("❗️ <b>Слишком коротко (минимум 15 символов)</b>\n\n" \
                                "Расскажи о сути проекта чуть подробнее. Не забывай: это увидят подписчики\n\n" \
                                "Попробуй ещё раз:",
                                parse_mode="HTML")
        else:
            await state.update_data(summ=summary)
            await state.set_state(ProjectSubmitState.waiting_for_uniq)
            await message.answer("7️⃣ <b>Почему проект крут (в чем его уникальность):</b>",
                        parse_mode="HTML")


@project_submit_router.message(ProjectSubmitState.waiting_for_uniq)
async def process_uniq(message: Message, state: FSMContext, db_session: AsyncSession):
    if message.text:
    
        uniq = message.text.strip()

        if len(uniq) > MAX_PROJ_UNIQ_SIZE:
            await message.answer(f"❗️ <b>Слишком много текста (максимум {MAX_PROJ_UNIQ_SIZE} симв.)</b>\n\n" \
                                "Постарайся уложиться в короткое и емкое описание — его увидят подписчики" \
                                "Попробуй ещё раз:",
                                parse_mode="HTML")
        elif len(uniq) < 15:
            await message.answer("❗️ <b>Слишком коротко (минимум 15 символов)</b>\n\n" \
                                "Расскажи о причине крутости проекта чуть подробнее. Не забывай: это увидят подписчики\n\n" \
                                "Попробуй ещё раз:",
                                parse_mode="HTML")
        else:

            await state.update_data(uniq=uniq)
            await state.set_state(ProjectSubmitState.waiting_for_check)

            user_data = await state.get_data()
            name = user_data["name"]
            link = user_data["link"]
            subtitle = user_data["subtitle"]
            summ = user_data["summ"]
            uniq = user_data["uniq"]

            await message.answer(
                                f"Проект в батле будет выглядеть вот так:\n\n"
                                f'🔢 <b><a href="{html.escape(link)}">{html.escape(name)} — {html.escape(subtitle)}</a></b>\n'
                                f"<b>👉 Суть: </b>{html.escape(summ)}\n"
                                f"<b>🔥 Почему круто: </b>{html.escape(uniq)}\n\n"
                                f"🔍 Проверь, всё верно?",
                                parse_mode="HTML", disable_web_page_preview=True, reply_markup=get_yes_no_keyboard())


@project_submit_router.callback_query(ProjectSubmitState.waiting_for_check, F.data == "confirm_yes")
async def process_yes_check_confirm(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession):

            user_data = await state.get_data()
            name = user_data["name"]
            link = user_data["link"]
            subtitle = user_data["subtitle"]
            summ = user_data["summ"]
            uniq = user_data["uniq"]

            cat_id = user_data["category_id"]
            scat_id = user_data["sub_category_id"]

            cat = user_data["category_name"]
            scat = user_data["sub_category_name"]

            await state.clear()

            project = Project(
                name=name,
                link=link,
                subtitle=subtitle,
                summ=summ,
                uniq=uniq,
                status=ProjectStatus.WAIT,
                category_id=cat_id,
                sub_category_id=scat_id,
                user_id=callback.from_user.id
            )
            db_session.add(project)

            await db_session.commit()

            await db_session.refresh(project)

            project_id = project.id
            
            payload = json.dumps({
                "_type": "project_submit",
                "user_id": callback.from_user.id,
                "username": callback.from_user.username,
                "project_id": project_id,
                "name": name,
                "link": link,
                "subtitle": subtitle,
                "summ": summ,
                "uniq": uniq,
                "cat": cat,
                "scat": scat
            })
            await redis_client.lpush("public_admin_moder_queue", payload)

            await callback.message.delete()

            await callback.message.answer("⏳ <b>Проект и заявка отправлены на модерацию</b>\n\n",
                                parse_mode="HTML",
                                reply_markup=get_main_keyboard())



@project_submit_router.callback_query(ProjectSubmitState.waiting_for_check, F.data == "confirm_no")
async def process_no_check_confirm(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession):

    await callback.message.edit_text("🔁 <b>Давай попробуем ещё раз</b>\n\n",
                                    parse_mode="HTML")

    await state.set_state(ProjectSubmitState.waiting_for_name)
    
    await callback.message.answer("3️⃣ <b>Название проекта:</b>",
                                parse_mode="HTML", reply_markup=get_cancel_keyboard())