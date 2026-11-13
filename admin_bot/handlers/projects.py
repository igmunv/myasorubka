from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from typing import Callable, Dict, Any, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import asyncio
import redis.asyncio as aioredis
import json, html
import math

from config import config

from public_bot_db.models import Project

from database.requests import get_all_projects

from aiogram.filters import Filter

projects_router = Router()

ALLOWED_USER_IDS = [config.superuser_tg_id, config.secret_spons_tg_id]
ITEMS_PER_PAGE = 2

redis_client = aioredis.from_url(f"redis://default:{config.redis_password.get_secret_value()}@redis:6379/0")

class IsAllowedUser(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ALLOWED_USER_IDS

projects_router.message.filter(IsAllowedUser())


@projects_router.message(StateFilter(None), F.text == "📁 Проекты")
async def cmd_projects(message: Message, state: FSMContext, db_session: AsyncSession):

    projects = await get_all_projects(session=db_session);

    await send_projects_msg(message, projects=projects, items_per_page=ITEMS_PER_PAGE)
                    
    

@projects_router.callback_query(F.data == "noop")
async def process_noop(callback: types.CallbackQuery):
    await callback.answer()


class ProjectsPagination(CallbackData, prefix="proj_page"):
    page: int



async def send_projects_msg(
    message: Message, projects: Project, page: int = 0, items_per_page: int = 3, update_msg: bool = False
):
    
    builder = InlineKeyboardBuilder()

    total_items = len(projects)
    total_pages = math.ceil(total_items / items_per_page) if total_items > 0 else 1

    # Защита от выходов за границы страниц
    page = max(0, min(page, total_pages - 1))

    # Срез категорий для текущей страницы
    start_offset = page * items_per_page
    end_offset = start_offset + items_per_page
    page_projects = projects[start_offset:end_offset]

    MSG_TEXT_PROJECTS = ""

    # Добавляем кнопки категорий (каждая с новой строки)
    for n, proj in enumerate(page_projects):
        if n == 0: num_emoji = "1️⃣"
        elif n == 1: num_emoji = "2️⃣"
        elif n == 2: num_emoji = "3️⃣"
        MSG_TEXT_PROJECTS += (
                            f'{num_emoji} <b><a href="{html.escape(proj.link)}">{html.escape(proj.name)} — {html.escape(proj.subtitle)}</a></b>\n'
                            f"<b>👉 Суть: </b>{html.escape(proj.summ)}\n"
                            f"<b>🔥 Почему круто: </b>{html.escape(proj.uniq)}\n\n"
                            )
        

    # Формируем навигационную строку
    nav_buttons = []

    # Кнопка «Назад»
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=ProjectsPagination(page=page - 1).pack(),
            )
        )
    else:
        nav_buttons.append(
            InlineKeyboardButton(text="⛔️", callback_data="noop")
        )  # заглушка

    # Счетчик страниц
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}", callback_data="noop"
        )
    )

    # Кнопка «Вперед»
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=ProjectsPagination(page=page + 1).pack(),
            )
        )

    else:
        nav_buttons.append(
            InlineKeyboardButton(text="⛔️", callback_data="noop")
        )  # заглушка

    builder.row(*nav_buttons)

    if update_msg:
        await message.edit_text(f"📁 <b>Проекты (сначала новые):</b>\n\n{MSG_TEXT_PROJECTS}", reply_markup=builder.as_markup(), parse_mode="HTML", disable_web_page_preview=True)
    else:
        await message.answer(f"📁 <b>Проекты (сначала новые):</b>\n\n{MSG_TEXT_PROJECTS}", reply_markup=builder.as_markup(), parse_mode="HTML", disable_web_page_preview=True)


# 2. Обработка переключения страниц (пагинация)
@projects_router.callback_query(ProjectsPagination.filter())
async def process_category_pagination(
    callback: types.CallbackQuery, callback_data: ProjectsPagination, db_session: AsyncSession
):
    projects = await get_all_projects(session=db_session);
    target_page = callback_data.page

    await send_projects_msg(callback.message, projects=projects, page=target_page, items_per_page=ITEMS_PER_PAGE, update_msg=True)

    await callback.answer()

