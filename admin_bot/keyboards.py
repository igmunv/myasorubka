from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup


def get_main_sponsr_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="📁 Проекты")
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)

