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
    buttons.append([InlineKeyboardButton(text="← Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_list_kb(products: list, category_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for prod in products:
        mark = "✓ " if prod["in_stock"] else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{mark}{prod['name']} — {prod['price']:,.0f} ₽",
                callback_data=f"prod_{prod['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="catalog")])
    buttons.append([InlineKeyboardButton(text="← Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_kb(
    product_id: int,
    category_id: int,
    photo_num: int = 0,
    total_photos: int = 1,
    is_fav: bool = False,
) -> InlineKeyboardMarkup:
    buttons = []

    # Навигация по фото
    if total_photos > 1:
        nav = []
        if photo_num > 0:
            nav.append(InlineKeyboardButton(
                text="◀", callback_data=f"prodphoto_{product_id}_{photo_num - 1}"
            ))
        nav.append(InlineKeyboardButton(
            text=f"📸 {photo_num + 1}/{total_photos}", callback_data="noop"
        ))
        if photo_num < total_photos - 1:
            nav.append(InlineKeyboardButton(
                text="▶", callback_data=f"prodphoto_{product_id}_{photo_num + 1}"
            ))
        buttons.append(nav)

    # Заказать
    buttons.append([InlineKeyboardButton(text="🛒 Заказать", callback_data=f"order_{product_id}")])

    # Избранное
    fav_text = "💔 Убрать из избранного" if is_fav else "❤️ В избранное"
    fav_cb   = f"unfav_{product_id}" if is_fav else f"fav_{product_id}"
    buttons.append([InlineKeyboardButton(text=fav_text, callback_data=fav_cb)])

    buttons.append([InlineKeyboardButton(text="← К товарам", callback_data=f"cat_{category_id}")])
    buttons.append([InlineKeyboardButton(text="← Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def search_results_kb(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for prod in products[:10]:
        mark = "✓ " if prod["in_stock"] else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{mark}{prod['name']} — {prod['price']:,.0f} ₽",
                callback_data=f"prod_{prod['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="← Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def favorites_kb(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for prod in products:
        mark = "✓ " if prod["in_stock"] else "✗ "
        buttons.append([
            InlineKeyboardButton(
                text=f"{mark}{prod['name']} — {prod['price']:,.0f} ₽",
                callback_data=f"prod_{prod['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="← Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
