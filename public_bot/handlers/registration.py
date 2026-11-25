from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import StateFilter

from sqlalchemy.ext.asyncio import AsyncSession

import json, html

from states import RegistrationState

from shared.db.models.user import User, UserStatus

import redis.asyncio as aioredis

from keyboards import get_main_keyboard, send_cancel_keyboard, get_go_keyboard, get_yes_no_keyboard

from shared.config import config

from valids import normalize_text, validate_text, validate_project_url, normalize_portfolio_url


registration_router = Router()

redis_client = aioredis.from_url(f"redis://default:{config.redis_password.get_secret_value()}@redis:6379/0")


MAX_NAME_SIZE = 32
MIN_NAME_SIZE = 3

MAX_ABOUT_SIZE = 250
MIN_ABOUT_SIZE = 40


@registration_router.message(RegistrationState(), F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🙅‍♂️ <b>Регистрация отменена</b>", 
                        parse_mode="HTML",
                        reply_markup=get_main_keyboard())


@registration_router.callback_query(StateFilter(None), F.data == "profile_registr")
async def process_butt_profile_registr(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession, user: User):

    if user.status == UserStatus.READY:
        await callback.message.answer(
            "⚠️ <b>Регистрация уже пройдена!</b>",
            parse_mode="HTML"
        )

    elif user.status == UserStatus.WAIT:
        await callback.message.answer(
            "🕘 <b>Ожидай решения модераторов</b>",
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


@registration_router.callback_query(RegistrationState.waiting_for_start, F.data == "go")
async def process_go_reg_or_edit(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession, user: User):

    if user.status == UserStatus.WAIT:
        await callback.message.answer(
            "⏳ <b>Профиль находится на проверке!</b>\n\nДождись решения модератора. Пока профиль проверяется, вносить изменения нельзя",
            parse_mode="HTML"
        )

    else:

        await state.set_state(RegistrationState.waiting_for_name)
        
        await callback.message.edit_text(
            "1️⃣ <b>Твоё имя или никнейм:</b>",
            parse_mode="HTML"
            )

        await callback.answer()


@registration_router.callback_query(StateFilter(None), F.data == "retry_registration")
async def process_retry_registration(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession, user: User):
    
    if user.status == UserStatus.WAIT:
        await callback.message.answer(
            "🕘 <b>Ожидай решения модераторов</b>",
            parse_mode="HTML"
        )

    else:
    
        await state.set_state(RegistrationState.waiting_for_name)

        await send_cancel_keyboard(callback.message)

        await callback.message.answer(
            "1️⃣ <b>Твоё имя или никнейм:</b>",
            parse_mode="HTML"
            )

    await callback.answer()


@registration_router.message(RegistrationState.waiting_for_name)
async def process_name(message: Message, state: FSMContext):

    if not message.text:
        await message.answer(
            "❗️ <b>Не увидел имени</b>\n\nПопробуй ввести ещё раз:",
            parse_mode="HTML",
        )
        return

    clean_name = normalize_text(message.text, capitalize_leading_ru=False, ensure_trailing_dot=False)
    error_reason = validate_text(clean_name, min_len=MIN_NAME_SIZE, max_len=MAX_NAME_SIZE)

    if error_reason:
        await message.answer(
            f"❗️ <b>Не могу принять ответ:</b> {error_reason}\n\nПопробуй ещё раз:",
            parse_mode="HTML",
        )
        return

    await state.update_data(name=clean_name)
    await state.set_state(RegistrationState.waiting_for_portfolio)
    await message.answer(
        "2️⃣ <b>Ссылка на тебя (ТГ-канал, GitHub, сайт и т.п.):</b>",
        parse_mode="HTML",
    )


@registration_router.message(RegistrationState.waiting_for_portfolio)
async def process_portfolio(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(
            "❗️ <b>Не увидел ссылку</b>\n\nПопробуй отправить ещё раз:",
            parse_mode="HTML",
        )
        return

    normalized_url = normalize_portfolio_url(message.text)
    error_reason = validate_project_url(normalized_url)

    if error_reason:
        await message.answer(
            f"❗️ <b>Не могу принять ссылку:</b> {error_reason}\n\nПопробуй ещё раз:",
            parse_mode="HTML",
        )
        return

    await state.update_data(portfolio=normalized_url)
    await state.set_state(RegistrationState.waiting_for_about)
    await message.answer(
        "3️⃣ <b>Пару слов о себе (опыт, чем занимаешься, стек):</b>",
        parse_mode="HTML",
    )


@registration_router.message(RegistrationState.waiting_for_about)
async def process_about(message: Message, state: FSMContext, db_session: AsyncSession, user: User):

    if not message.text:
        await message.answer(
            "❗️ <b>Не увидел текст</b>\n\nПопробуй ввести ещё раз:",
            parse_mode="HTML",
        )
        return

    clean_about = normalize_text(message.text)
    error_reason = validate_text(clean_about, min_len=MIN_ABOUT_SIZE, max_len=MAX_ABOUT_SIZE)

    if error_reason:
        await message.answer(
            f"❗️ <b>Не могу принять ответ:</b> {error_reason}\n\nПопробуй ещё раз:",
            parse_mode="HTML",
        )
        return
    
    user_data = await state.get_data()
    name = user_data["name"]
    portfolio = user_data["portfolio"]

    await state.update_data(about=clean_about)
    await state.set_state(RegistrationState.waiting_for_check)

    await message.answer(

        f"Твоя карточка при выигрыше будет выглядеть вот так 👇\n\n"
        f'<blockquote>🏆 <b>Победитель МЯСОРУБКИ #123</b>\n\n'
        f"Здесь будет описание твоего проекта...\n\n"
        f"🥇 <b>Автор:</b> {html.escape(name)}\n"
        f"💬 <b>О себе:</b> {html.escape(clean_about)}\n"
        f'<b><a href="{html.escape(portfolio)}">🔗 Найти меня можно здесь</a></b>\n\n'
        f'⭐️ <b>Давайте поддержим автора и его проект!</b></blockquote>\n\n'
        f"🔍 Проверь, всё верно?",

        parse_mode="HTML", disable_web_page_preview=True, reply_markup=get_yes_no_keyboard())


@registration_router.callback_query(RegistrationState.waiting_for_check, F.data == "confirm_no")
async def process_no_check_confirm(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession, user: User):

    await callback.answer()

    await callback.message.edit_text("🔁 <b>Давай попробуем ещё раз</b>\n\n",
                                        parse_mode="HTML")
    
    await state.set_state(RegistrationState.waiting_for_name)
    
    await callback.message.answer(
                "1️⃣ <b>Твоё имя или никнейм:</b>",
                parse_mode="HTML"
                )

    
@registration_router.callback_query(RegistrationState.waiting_for_check, F.data == "confirm_yes")
async def process_yes_check_confirm(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession, user: User):

    user_data = await state.get_data()
    name = user_data["name"]
    portfolio = user_data["portfolio"]
    about = user_data["about"]

    await callback.answer()

    if user:
        user.name = name
        user.portfolio = portfolio
        user.about = about
        user.status = UserStatus.WAIT

    else:
        user = User(
            id=callback.from_user.id,
            name=name,
            portfolio=portfolio,
            about=about,
            status=UserStatus.WAIT
        )
        db_session.add(user)

    await db_session.commit()

    payload = json.dumps({
        "_type": "registration",
        "user_id": callback.from_user.id,
        "name": user_data["name"],
        "portfolio": user_data["portfolio"],
        "about": about
    })
    await redis_client.lpush("public_admin_moder_queue", payload)

    await state.clear()

    await callback.message.answer("⏳ <b>Отправлено на модерацию</b>\n\n" \
                        "Проверяем профиль. После проверки — сможешь скинуть свой проект на мясорубку!",
                        parse_mode="HTML",
                        reply_markup=get_main_keyboard())