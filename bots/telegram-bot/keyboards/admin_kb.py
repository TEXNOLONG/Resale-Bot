from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 Товары", callback_data="adm_products"),
            InlineKeyboardButton(text="🗂 Категории", callback_data="adm_categories"),
        ],
        [
            InlineKeyboardButton(text="⭐ Отзывы", callback_data="adm_reviews"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats"),
        ],
        [
            InlineKeyboardButton(text="🛒 Заказы", callback_data="adm_orders"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="adm_settings"),
        ],
        [
            InlineKeyboardButton(text="📋 Скачать логи", callback_data="adm_logs"),
        ],
        [
            InlineKeyboardButton(text="🏠 Вернуться в бот", callback_data="main_menu"),
        ],
    ])


def admin_products_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="adm_add_product")],
        [InlineKeyboardButton(text="✏️ Редактировать товар", callback_data="adm_edit_product")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="adm_del_product")],
        [InlineKeyboardButton(text="📋 Все товары", callback_data="adm_list_products")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm_back")],
    ])


def admin_categories_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить категорию", callback_data="adm_add_category")],
        [InlineKeyboardButton(text="🗑 Удалить категорию", callback_data="adm_del_category")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm_back")],
    ])


def admin_reviews_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Ожидающие одобрения", callback_data="adm_pending_reviews")],
        [InlineKeyboardButton(text="✅ Одобренные отзывы", callback_data="adm_approved_reviews")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm_back")],
    ])


def admin_settings_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼 Приветственное фото", callback_data="adm_set_photo")],
        [InlineKeyboardButton(text="📝 Приветственный текст", callback_data="adm_set_welcome_text")],
        [InlineKeyboardButton(text="🔧 Фото панели администратора", callback_data="adm_set_admin_photo")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="adm_set_contact")],
        [InlineKeyboardButton(text="ℹ️ Текст «О нас»", callback_data="adm_set_about")],
        [InlineKeyboardButton(text="🖼 Фото «О нас»", callback_data="adm_set_about_photo")],
        [InlineKeyboardButton(text="📢 Канал с отзывами", callback_data="adm_set_reviews_channel")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm_back")],
    ])


def admin_orders_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Последние заказы", callback_data="adm_list_orders")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm_back")],
    ])


def order_reply_kb(order_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Написать покупателю", callback_data=f"adm_reply_{order_id}_{user_id}")]
    ])


def categories_select_kb(categories: list, prefix: str = "adm_selcat") -> InlineKeyboardMarkup:
    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(
                text=f"{cat['emoji']} {cat['name']}",
                callback_data=f"{prefix}_{cat['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Отмена", callback_data="adm_products")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_select_kb(products: list, prefix: str, back_cb: str = "adm_products") -> InlineKeyboardMarkup:
    buttons = []
    for prod in products[:20]:
        stock = "✅" if prod["in_stock"] else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{stock} {prod['name']} — {prod['price']:,.0f} ₽",
                callback_data=f"{prefix}_{prod['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Отмена", callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def edit_product_fields_kb(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Название", callback_data=f"adm_edit_name_{product_id}")],
        [InlineKeyboardButton(text="📄 Описание", callback_data=f"adm_edit_desc_{product_id}")],
        [InlineKeyboardButton(text="💰 Цена", callback_data=f"adm_edit_price_{product_id}")],
        [InlineKeyboardButton(text="🔄 Наличие (вкл/выкл)", callback_data=f"adm_toggle_stock_{product_id}")],
        [InlineKeyboardButton(text="📁 Папка с фото", callback_data=f"adm_edit_folder_{product_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm_products")],
    ])


def review_actions_kb(review_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_approve_rev_{review_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"adm_del_rev_{review_id}"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm_reviews")],
    ])


def back_to_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в админку", callback_data="adm_back")]
    ])


def cancel_kb(back_cb: str = "adm_back") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=back_cb)]
    ])


def confirm_delete_kb(item_id: int, item_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"adm_confirm_del_{item_type}_{item_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="adm_products"),
        ]
    ])
