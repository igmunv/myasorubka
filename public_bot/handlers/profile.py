from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import StateFilter

from states import RegistrationState

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import get_cancel_keyboard, get_main_keyboard, get_profile_keyboard

from database.models import User, UserStatus

import redis.asyncio as aioredis

from config import config

import html

from admin_bot_db.models import RegistrationModeration

profile_router = Router()


@profile_router.message(StateFilter(None), F.text == "👤 Профиль")
async def cmd_profile(message: Message, state: FSMContext, db_session: AsyncSession):
    user = await db_session.get(User, message.from_user.id)

    if user.status == UserStatus.NEW:
        await message.answer(f"👤 Сначала нужно зарегистрироваться", 
                             reply_markup=get_profile_keyboard(is_regstr=False)
                            )
        return

    elif user.status == UserStatus.FAIL:
        moder_status = " (<i>модерация не пройдена ❌</i>)"
        record = await db_session.get(RegistrationModeration, message.from_user.id)

        await message.answer(f"👤 <b>Твой профиль {moder_status}:</b>\n\n"
                            f"Для участия в батлах, необходимо <b>обязательно пройти регистрацию</b>. "
                            f"Посмотри причину неудачной проверки, и попробуй решить её:\n\n"
                            f"<blockquote>{record.reason}</blockquote>\n\n"
                            f"Данные, которые ты вводил:\n\n"
                            f"👤 <b>Имя:</b> {html.escape(user.name)}\n"
                            f"💬 <b>О себе:</b> {html.escape(user.about)}\n"
                            f'🔗 <b>Ссылка:</b>{html.escape(user.portfolio)}', 
                            reply_markup=get_profile_keyboard(),
                            parse_mode="HTML",
                            disable_web_page_preview=True
                        )

        return
        
    elif user.status == UserStatus.WAIT:
        moder_status = " (<i>на модерации 🕘</i>)"

    elif user.status == UserStatus.READY:
        moder_status = " (<i>проверено ✅</i>)"
        
    await message.answer(f"👤 <b>Твой профиль {moder_status}:</b>\n\n"
                        f"Так будет выглядеть твоя карточка в канале, если ты выиграешь батл 👇\n\n"
                        f"<blockquote>🏛 <b>Зал славы: Название твоего проекта</b>\n\n"
                        f"Здесь будет описание твоего проекта и причина его крутости...\n\n"
                        f"🥇 <b>Победитель:</b> {html.escape(user.name)}\n"
                        f"💬 <b>О себе:</b> {html.escape(user.about)}\n"
                        f'<b><a href="{html.escape(user.portfolio)}">🔗 Найти меня можно здесь</a></b></blockquote>\n\n'
                        f"💡 Хочешь что-то поправить или посмотреть свои проекты? Жми кнопки ниже", 
                        reply_markup=get_profile_keyboard(),
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )


@profile_router.callback_query(StateFilter(None), F.data == "profile_registr")
async def process_butt_profile_registr_or_change(callback: types.CallbackQuery, state: FSMContext, db_session: AsyncSession):

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
    
        await state.set_state(RegistrationState.waiting_for_name)

        await callback.message.answer(
            "1️⃣ <b>Твоё имя или никнейм:</b>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
            )

    await callback.answer()