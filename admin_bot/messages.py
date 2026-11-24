import asyncio
import json

import redis.asyncio as aioredis

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import html

from shared.config import config

from shared.db.models.project import Project
from shared.db.models.user import User


async def send_user_reg_approval_form(bot: Bot, chat_id: int, user_id: int, 
                                      name: str, portfolio: str, about: str
                                      ):

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"mod_registration_approve:{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod_registration_reject:{user_id}")
        ]
    ])

    # Отправляем карточку в чат модераторов
    await bot.send_message(
        chat_id=chat_id,
        text=(
            f"🚨 <b>Новый участник на мясорубку!</b>\n\n"
            f"👤 Имя: <b>{html.escape(name)}</b>\n"
            f"🔗 Портфолио: {html.escape(portfolio)}\n"
            f"📝 О себе: {html.escape(about)}\n"
            f"🆔 ID: <code>{user_id}</code>"
        ),
        parse_mode="HTML",
        reply_markup=kb, 
        disable_web_page_preview=True
    )


async def send_project_approval_form(bot: Bot, chat_id: int, user_id: int, 
                                     project_id: int, link: str, name: str, 
                                     subtitle: str, summ: str, uniq: str, 
                                     cat: str, scat: str
                                     ):

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"mod_project_submit_approve:{user_id}:{project_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod_project_submit_reject:{user_id}:{project_id}")
        ]
    ])

    await bot.send_message(
        chat_id=chat_id,
        text=(
            f"🆕 <b>Новый проект на мясорубку!</b>\n\n"
            f'🔢 <b><a href="{html.escape(link)}">{html.escape(name)} — {html.escape(subtitle)}</a></b>\n'
            f"<b>👉 Суть: </b>{html.escape(summ)}\n"
            f"<b>🔥 Почему круто: </b>{html.escape(uniq)}\n\n"
            f"📁 <b>Категория: </b>{html.escape(cat)}\n"
            f"🏷️ <b>Подкатегория: </b>{html.escape(scat)}\n"
        ),
        parse_mode="HTML",
        reply_markup=kb, 
        disable_web_page_preview=True
    )