from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛍 Товары", callback_data="catalog"),
            InlineKeyboardButton(text="🔍 Поиск", callback_data="search"),
        ],
        [
            InlineKeyboardButton(text="⭐ Отзывы", callback_data="reviews"),
            InlineKeyboardButton(text="📩 Контакты", callback_data="contacts"),
        ],
    ])


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Главное меню", callback_data="main_menu")]
    ])
