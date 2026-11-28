from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отмена")
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def get_main_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="Новый Батл")
    
    # builder.button(text="🏆 Зал славы")
    # builder.button(text="👤 Профиль")
    
    # builder.adjust(1, 2)
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)