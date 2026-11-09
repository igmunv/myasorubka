from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup
import math
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отмена")
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def get_main_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📁 Отправить проект")
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)

# да, ИИ, и что бля? работает же

class CategoryPagination(CallbackData, prefix="cat_page"):
    page: int

class CategorySelect(CallbackData, prefix="cat_select"):
    id: int


def get_categories_keyboard(
    categories: list[dict], page: int = 0, items_per_page: int = 5
) -> InlineKeyboardMarkup:
    """Генератор сетки категорий с пагинацией.

    :param categories: список словарей вида [{'id': 1, 'name': 'Категория 1'},
    ...]
    :param page: текущая страница (начиная с 0)
    :param items_per_page: количество категорий на одной странице
    """
    builder = InlineKeyboardBuilder()

    total_items = len(categories)
    total_pages = math.ceil(total_items / items_per_page) if total_items > 0 else 1

    # Защита от выходов за границы страниц
    page = max(0, min(page, total_pages - 1))

    # Срез категорий для текущей страницы
    start_offset = page * items_per_page
    end_offset = start_offset + items_per_page
    page_categories = categories[start_offset:end_offset]

    # Добавляем кнопки категорий (каждая с новой строки)
    for cat in page_categories:
        builder.button(
            text=cat["name"],
            callback_data=CategorySelect(id=cat["id"]).pack(),
        )
    builder.adjust(1)  # по 1 кнопке в ряду для категорий

    # Формируем навигационную строку
    nav_buttons = []

    # Кнопка «Назад»
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=CategoryPagination(page=page - 1).pack(),
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
                callback_data=CategoryPagination(page=page + 1).pack(),
            )
        )
    else:
        nav_buttons.append(
            InlineKeyboardButton(text="⛔️", callback_data="noop")
        )  # заглушка

    builder.row(*nav_buttons)

    return builder.as_markup()