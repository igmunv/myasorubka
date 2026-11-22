from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import StateFilter

from states import RegistrationState

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import send_cancel_keyboard, get_project_keyboard, get_profile_keyboard, get_go_keyboard, get_registration_button, get_retry_registration_keyboard
from keyboards import ProjectPaginationCallback

from shared.db.models.user import User, UserStatus
from shared.db.models.project import ProjectStatus, Project, Category, SubCategory
from shared.db.models.moderation import RegistrationModeration, ProjectsModeration
from shared.db.requests.project import get_user_projects

import html

profile_router = Router()


@profile_router.message(StateFilter(None), F.text == "👤 Профиль")
async def cmd_profile(message: Message, state: FSMContext, db_session: AsyncSession, user: User):

    if user.status == UserStatus.NEW:
        await message.answer(f"👤 Сначала нужно зарегистрироваться", 
                             reply_markup=get_profile_keyboard(is_regstr=False)
                            )

    elif user.status == UserStatus.FAIL:
        record = await db_session.get(RegistrationModeration, message.from_user.id)
        await message.answer(f"👤 <b>Твой профиль (<i>модерация не пройдена ❌</i>):</b>\n\n"
                            f"Для участия в батлах, необходимо <b>обязательно пройти регистрацию</b>. "
                            f"Посмотри причину неудачной проверки, и попробуй решить её:\n\n"
                            f"<blockquote>{record.reason}</blockquote>\n\n"
                            f"Данные, которые ты вводил:\n\n"
                            f"👤 <b>Имя:</b> {html.escape(user.name)}\n"
                            f"💬 <b>О себе:</b> {html.escape(user.about)}\n"
                            f'🔗 <b>Ссылка:</b> {html.escape(user.portfolio)}', 
                            reply_markup=get_retry_registration_keyboard(),
                            parse_mode="HTML",
                            disable_web_page_preview=True
                        )
        
    elif user.status == UserStatus.WAIT:
        await message.answer(f"👤 <b>Твой профиль (<i>на модерации 🕘</i>):</b>\n\n"
                            f"Так будет выглядеть твоя карточка в канале, если ты выиграешь батл 👇\n\n"
                            f"<blockquote>🏛 <b>Зал славы: Название твоего проекта</b>\n\n"
                            f"Здесь будет описание твоего проекта и причина его крутости...\n\n"
                            f"🥇 <b>Победитель:</b> {html.escape(user.name)}\n"
                            f"💬 <b>О себе:</b> {html.escape(user.about)}\n"
                            f'<b><a href="{html.escape(user.portfolio)}">🔗 Найти меня можно здесь</a></b>\n\n'
                            f'⭐️ <b>Давайте поддержим автора и его проект!</b></blockquote>\n\n'
                            f"💡 Пока профиль не прошел модерацию, его нельзя редактировать", 
                            parse_mode="HTML",
                            disable_web_page_preview=True
                        )

    elif user.status == UserStatus.READY:
        await message.answer(f"👤 <b>Твой профиль (<i>проверено ✅</i>):</b>\n\n"
                            f"Так будет выглядеть твоя карточка в канале, если ты выиграешь батл 👇\n\n"
                            f"<blockquote>🏆 <b>Победитель МЯСОРУБКИ #123</b>\n\n"
                            f"Здесь будет описание твоего проекта...\n\n"
                            f"🥇 <b>Автор:</b> {html.escape(user.name)}\n"
                            f"💬 <b>О себе:</b> {html.escape(user.about)}\n"
                            f'<b><a href="{html.escape(user.portfolio)}">🔗 Найти меня можно здесь</a></b>\n\n'
                            f'⭐️ <b>Давайте поддержим автора и его проект!</b></blockquote>\n\n'
                            f"💡 Хочешь что-то поправить или посмотреть свои проекты? Жми кнопки ниже", 
                            reply_markup=get_profile_keyboard(),
                            parse_mode="HTML",
                            disable_web_page_preview=True
                        )


@profile_router.callback_query(StateFilter(None), F.data == "profile_edit")
async def process_butt_profile_edit(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession, user: User):

    if user.status == UserStatus.NEW:
        await callback.message.answer(
            "⚠️ <b>Сначала нужно зарегистрироваться!</b>",
            parse_mode="HTML",
            reply_markup=get_registration_button()
        )

    elif user.status == UserStatus.WAIT:
        await callback.message.answer(
            "⏳ <b>Профиль находится на проверке!</b>\n\nДождись решения модератора. Пока профиль проверяется, вносить изменения нельзя",
            parse_mode="HTML"
        )

    else:

        await state.set_state(RegistrationState.waiting_for_start)

        await send_cancel_keyboard(callback.message)
        
        await callback.message.answer(
            "🔥 <b>Если твой проект победит — этот профиль улетит в отдельный пост на весь канал!</b> Заполняй сразу красиво и без ошибок, чтобы забрать максимум трафика",
            parse_mode="HTML",
            reply_markup=get_go_keyboard()
        )

    await callback.answer()



async def format_project_text(project: Project, db_session, total_count, current_index) -> str:

    header = f"📂 <b>Проект {current_index + 1} из {total_count}</b>\n\n"

    if project.status == ProjectStatus.WAIT: status = "на модерации 🕘"
    elif project.status == ProjectStatus.FAIL: status = "модерация не пройдена ❌"
    elif project.status == ProjectStatus.READY: status = "проверено ✅"
    elif project.status == ProjectStatus.ON_BATTLE: status = "на батле 🥩"
    elif project.status == ProjectStatus.POST_BATTLE: status = "после батла 🏖"

    category = await db_session.get(Category, project.category_id)
    category_name = category.name if category else "Не указана"

    sub_category = await db_session.get(SubCategory, project.sub_category_id)
    sub_category_name = sub_category.name if sub_category else "Не указана"

    TEXT = (
        f'🔢 <b><a href="{html.escape(project.link)}">{html.escape(project.name)} — {html.escape(project.subtitle)}</a></b>\n'
        f"<b>👉 Суть: </b>{html.escape(project.summ)}\n"
        f"<b>🔥 Почему круто: </b>{html.escape(project.uniq)}\n\n"
        f"<b>📁 Категория: </b>{html.escape(category_name)}\n"
        f"<b>🏷️ Подкатегория: </b>{html.escape(sub_category_name)}\n\n"
        f"<b>Статус: </b><i>{html.escape(status)}</i>\n"
    )

    if project.status == ProjectStatus.FAIL:
        record = await db_session.get(ProjectsModeration, project.id)
        reason_text = record.reason if record else "Причина не указана"
        TEXT += f"<b>Причина:\n</b><blockquote>{html.escape(reason_text)}</blockquote>"

    return header + TEXT



@profile_router.callback_query(StateFilter(None), F.data == "profile_projects")
async def process_butt_my_projects(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession):
    projects = await get_user_projects(db_session, callback.from_user.id)

    if not projects:
        await callback.message.answer("🦗 <b>У тебя пока нет ни одного добавленного проекта</b>",
        parse_mode="HTML")
        await callback.answer()
        return
        
    # 3. Берем первый проект (индекс 0)
    current_index = 0
    current_project = projects[current_index]
    
    # 4. Формируем текст и клавиатуру с помощью наших функций из прошлого шага
    text = await format_project_text(current_project, db_session, len(projects), current_index=current_index)
    keyboard = get_project_keyboard(current_index, len(projects), current_project.id)
    
    # 5. Отправляем сообщение пользователю
    await callback.message.answer(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    await callback.answer()



@profile_router.callback_query(ProjectPaginationCallback.filter())
async def process_pagination(callback: types.CallbackQuery, callback_data: ProjectPaginationCallback, db_session: AsyncSession):
    user_id = callback.from_user.id
    target_index = callback_data.index
    
    # 1. Получаем все актуальные проекты пользователя из базы
    projects = await get_user_projects(db_session, user_id) # Твоя функция выборки
    
    if not projects:
        await callback.answer("У тебя больше нет проектов", show_alert=True)
        await callback.message.delete()
        return

    # Защита на случай, если индекс вышел за рамки (например, проект удалили параллельно)
    if target_index >= len(projects):
        target_index = 0
        
    current_project = projects[target_index]
    
    # 2. Формируем новый текст и клавиатуру
    text = await format_project_text(current_project, db_session, len(projects), current_index=target_index)
    keyboard = get_project_keyboard(target_index, len(projects), current_project.id)
    
    # 3. Обновляем сообщение (вместо отправки нового!)
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    await callback.answer() # Убираем часики с кнопки