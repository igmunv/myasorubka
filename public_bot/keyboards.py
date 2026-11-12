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
    
    builder.button(text="🚀 Отправить проект")
    
    builder.button(text="🏆 Зал славы")
    builder.button(text="👤 Профиль")
    
    builder.adjust(1, 2)
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)

# да, ИИ, и что бля? работает же

class CategoryPagination(CallbackData, prefix="cat_page"):
    page: int

class SubCategoryPagination(CallbackData, prefix="subcat_page"):
    page: int

class CategorySelect(CallbackData, prefix="cat_select"):
    id: int

class SubCategorySelect(CallbackData, prefix="subcat_select"):
    id: int


def get_categories_keyboard(
    categories: list[dict], page: int = 0, items_per_page: int = 5, is_subcat=False
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
        if not is_subcat:
            builder.button(
                text=cat["name"],
                callback_data=CategorySelect(id=cat["id"]).pack(),
            )
        else:
            builder.button(
                text=cat["name"],
                callback_data=SubCategorySelect(id=cat["id"]).pack(),
            )
    builder.adjust(1)  # по 1 кнопке в ряду для категорий

    builder.row(
        InlineKeyboardButton(
            text="❌ Нет подходящей", callback_data="no_category_chosen"
        )
    )

    # Формируем навигационную строку
    nav_buttons = []

    # Кнопка «Назад»
    if page > 0:
        if not is_subcat:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=CategoryPagination(page=page - 1).pack(),
                )
            )
        else:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=SubCategoryPagination(page=page - 1).pack(),
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
        if not is_subcat:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="Вперед ➡️",
                    callback_data=CategoryPagination(page=page + 1).pack(),
                )
            )
        else:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="Вперед ➡️",
                    callback_data=SubCategoryPagination(page=page + 1).pack(),
                )
            )
    else:
        nav_buttons.append(
            InlineKeyboardButton(text="⛔️", callback_data="noop")
        )  # заглушка

    builder.row(*nav_buttons)

    return builder.as_markup()


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки с callback_data для отслеживания нажатий
    builder.button(text="✅ Да", callback_data="confirm_yes")
    builder.button(text="❌ Нет", callback_data="confirm_no")
    
    # Располагаем их в один ряд (по 2 кнопки в строке)
    builder.adjust(2)
    
    return builder.as_markup()


def get_go_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки с callback_data для отслеживания нажатий
    builder.button(text="Погнали!", callback_data="go")
    
    return builder.as_markup()

def get_retry_registration_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки с callback_data для отслеживания нажатий
    builder.button(text="🔄 Попробовать еще раз", callback_data="retry_registration")
    
    return builder.as_markup()

def get_profile_keyboard(is_regstr=True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if is_regstr:
        builder.button(text="✏️ Редактировать", callback_data="profile_change")
        builder.button(text="📁 Мои Проекты", callback_data="profile_projects")
        builder.adjust(2)
    else:
        builder.button(text="➕ Регистрация", callback_data="profile_registr")
    
    return builder.as_markup()