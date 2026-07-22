from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def categories_kb(categories: list) -> InlineKeyboardMarkup:
    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(
                text=f"{cat['emoji']} {cat['name']}",
                callback_data=f"cat_{cat['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="← Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_list_kb(products: list, category_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for prod in products:
        stock = "✓" if prod["in_stock"] else "✗"
        buttons.append([
            InlineKeyboardButton(
                text=f"{stock} {prod['name']} — {prod['price']:,.0f} ₽",
                callback_data=f"prod_{prod['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="catalog")])
    buttons.append([InlineKeyboardButton(text="← Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_kb(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить / Узнать подробнее", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton(text="← Назад к товарам", callback_data=f"cat_{category_id}")],
        [InlineKeyboardButton(text="← Главное меню", callback_data="main_menu")],
    ])


def buy_kb(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Назад к товару", callback_data=f"prod_{product_id}")],
    ])


def search_results_kb(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for prod in products[:10]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{prod['name']} — {prod['price']:,.0f} ₽",
                callback_data=f"prod_{prod['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="← Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
