from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import StateFilter

from sqlalchemy.ext.asyncio import AsyncSession

import validators
import json

from states import RegistrationState

from database.models import User, UserStatus

import redis.asyncio as aioredis

from keyboards import get_main_keyboard, send_cancel_keyboard, get_go_keyboard

from config import config


registration_router = Router()

redis_client = aioredis.from_url(f"redis://default:{config.redis_password.get_secret_value()}@redis:6379/0")


@registration_router.message(RegistrationState(), F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🙅‍♂️ <b>Регистрация отменена</b>", 
                        parse_mode="HTML",
                        reply_markup=get_main_keyboard())


@registration_router.callback_query(StateFilter(None), F.data == "profile_registr")
async def process_butt_profile_registr(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession):

    user = await db_session.get(User, callback.from_user.id)

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
async def process_go_reg_or_edit(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession):
    await state.set_state(RegistrationState.waiting_for_name)
    
    await callback.message.edit_text(
        "1️⃣ <b>Твоё имя или никнейм:</b>",
        parse_mode="HTML"
        )

    await callback.answer()


@registration_router.callback_query(StateFilter(None), F.data == "retry_registration")
async def process_retry_registration(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession):
    
    await state.set_state(RegistrationState.waiting_for_name)

    await send_cancel_keyboard(callback.message)

    await callback.message.answer(
        "1️⃣ <b>Твоё имя или никнейм:</b>",
        parse_mode="HTML"
        )

    await callback.answer()


@registration_router.message(RegistrationState.waiting_for_name)
async def process_name(message: Message, state: FSMContext):

    if message.text:

        name = message.text.strip()

        if len(name) > 32:
            await message.answer("❗️ <b>Имя слишком длинное (максимум 32 символа)</b>\n\nПопробуй ввести ещё раз:",
                                parse_mode="HTML")
        elif len(name) < 3:
            await message.answer("❗️ <b>Имя слишком короткое (минимум 3 символа)</b>\n\nПопробуй ввести ещё раз:",
                                parse_mode="HTML")
        else:
            await state.update_data(name=name)
            await state.set_state(RegistrationState.waiting_for_portfolio)
            await message.answer("2️⃣ <b>Ссылка на портфолио (GitHub, сайт или резюме):</b>",
                                parse_mode="HTML")

    else:
        await message.answer("❗️ <b>Не увидел имени</b>\n\nПопробуй ввести ещё раз:",
                            parse_mode="HTML")


@registration_router.message(RegistrationState.waiting_for_portfolio)
async def process_portfolio(message: Message, state: FSMContext):

    if message.text:

        url = message.text.strip()
    
        if validators.url(url):
            await state.update_data(portfolio=url)
            await state.set_state(RegistrationState.waiting_for_about)
            await message.answer("3️⃣ <b>Пару слов о себе (опыт, чем занимаешься, стек):</b>",
                                            parse_mode="HTML")

        else:
            await message.answer("❗️ <b>Это не ссылка</b>\n\nПопробуй ещё раз:",
                                parse_mode="HTML")
    else:
        await message.answer("❗️ <b>Не увидел ссылку</b>\n\nПопробуй отправить ещё раз:",
                            parse_mode="HTML")

@registration_router.message(RegistrationState.waiting_for_about)
async def process_about(message: Message, state: FSMContext, db_session: AsyncSession):

    if message.text:

        about = message.text.strip()

        if len(about) > 250:
            await message.answer("❗️ <b>Слишком много текста (максимум 250 символов)</b>\n\n" \
                                "Постарайся уложиться в короткую и емкую визитку — именно её увидят подписчики в случае победы!" \
                                "Попробуй ещё раз:",
                                parse_mode="HTML")
        elif len(about) < 15:
            await message.answer("❗️ <b>Слишком коротко (минимум 15 символов)</b>\n\n" \
                                "Расскажи о себе чуть подробнее. Не забывай: если твой проект победит, эта визитка будет в посте на канале!\n\n" \
                                "Попробуй ещё раз:",
                                parse_mode="HTML")
        else:
            user_data = await state.get_data()
            name = user_data["name"]
            portfolio = user_data["portfolio"]

            await state.clear()

            user = await db_session.get(User, message.from_user.id)

            if user:
                user.name = name
                user.portfolio = portfolio
                user.about = about
                user.status = UserStatus.WAIT

            else:
                user = User(
                    id=message.from_user.id,
                    name=name,
                    portfolio=portfolio,
                    about=about,
                    status=UserStatus.WAIT
                )
                db_session.add(user)

            await db_session.commit()

            payload = json.dumps({
                "_type": "registration",
                "user_id": message.from_user.id,
                "name": user_data["name"],
                "portfolio": user_data["portfolio"],
                "about": about
            })
            await redis_client.lpush("public_admin_moder_queue", payload)

            await message.answer("⏳ <b>Отправлено на модерацию</b>\n\n" \
                                "Проверяем профиль. После проверки — сможешь скинуть свой проект на мясорубку!",
                                parse_mode="HTML",
                                reply_markup=get_main_keyboard())

    else:
        await message.answer("❗️ <b>Не увидел текст</b>\n\nПопробуй ввести ещё раз:",
                            parse_mode="HTML")