from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, CallbackQuery

from typing import Callable, Dict, Any, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import asyncio
import redis.asyncio as aioredis
import json, html

from states import RegRejectedState, ProjSubmitRejectState

from shared.config import config

from shared.db.models.project import Project, ProjectStatus
from shared.db.models.user import User, UserStatus

from shared.db.requests.user import get_next_waiting_user
from shared.db.requests.project import get_next_waiting_project

from keyboards import get_main_sponsr_keyboard

from aiogram.filters import Filter

from messages import send_user_reg_approval_form, send_project_approval_form

getters_router = Router()


ALLOWED_USER_IDS = [config.superuser_tg_id]

redis_client = aioredis.from_url(f"redis://default:{config.redis_password.get_secret_value()}@redis:6379/0")


class IsAllowedUser(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ALLOWED_USER_IDS

getters_router.message.filter(IsAllowedUser())

@getters_router.message(F.text == "ЮЗЕРЫ")
async def handle_users_button(message: Message, state: FSMContext, db_session: AsyncSession) -> None:

    waiting_user: User = await get_next_waiting_user(db_session)

    if waiting_user:
        await send_user_reg_approval_form(message.bot, config.superuser_tg_id, 
                                    waiting_user.id, waiting_user.name, 
                                    waiting_user.portfolio, waiting_user.about
                                    )
    else:
        await message.answer("пусто")


@getters_router.message(F.text == "ПРОЕКТЫ")
async def handle_projects_button(message: Message, state: FSMContext, db_session: AsyncSession) -> None:

    waiting_project: Project = await get_next_waiting_project(db_session)

    if waiting_project:
        await send_project_approval_form(message.bot, config.superuser_tg_id, waiting_project.user_id, waiting_project.id, 
                                    waiting_project.link, waiting_project.name, waiting_project.subtitle, waiting_project.summ, 
                                    waiting_project.uniq, waiting_project.category.name, waiting_project.sub_category.name
                                    )

    else:
        await message.answer("пусто")