from aiogram import Router, F
from aiogram.types import CallbackQuery

import database as db
from keyboards.catalog_kb import (
    categories_kb, products_list_kb, product_detail_kb
)

router = Router()

# ─── helpers ──────────────────────────────────────────────────────────────────

async def safe_text(callback: CallbackQuery, text: str, kb):
    """Edit existing message to text; if it's a photo message — delete + resend."""
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")


async def safe_photo(callback: CallbackQuery, photo: str, caption: str, kb):
    """Always delete current message and send a fresh photo card."""
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer_photo(
        photo, caption=caption, reply_markup=kb, parse_mode="HTML"
    )


# ─── catalog ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "catalog")
async def cb_catalog(callback: CallbackQuery):
    await callback.answer()
    categories = await db.get_categories()
    if not categories:
        from keyboards.main_kb import back_to_menu_kb
        await safe_text(callback, "Категорий пока нет. Зайдите позже.", back_to_menu_kb())
        return
    await safe_text(callback, "<b>Каталог</b>\n\nВыберите категорию:", categories_kb(categories))


@router.callback_query(F.data.startswith("cat_"))
async def cb_category(callback: CallbackQuery):
    await callback.answer()
    category_id = int(callback.data.split("_")[1])
    category = await db.get_category(category_id)
    products = await db.get_products_by_category(category_id)

    if not products:
        categories = await db.get_categories()
        await safe_text(
            callback,
            f"В категории <b>{category['name']}</b> пока нет товаров.",
            categories_kb(categories)
        )
        return

    cat_name = f"{category['emoji']} {category['name']}" if category else "Категория"
    await safe_text(
        callback,
        f"<b>{cat_name}</b>\n\nТоваров: {len(products)}",
        products_list_kb(products, category_id)
    )


@router.callback_query(F.data.startswith("prod_"))
async def cb_product(callback: CallbackQuery):
    await callback.answer()
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)

    if not product:
        await safe_text(callback, "Товар не найден.", None)
        return

    await db.increment_views(product_id)
    await db.add_product_click(product_id, callback.from_user.id)

    stock_text = "В наличии ✓" if product["in_stock"] else "Нет в наличии"
    price_fmt = f"{product['price']:,.0f}".replace(",", " ")

    caption = (
        f"<b>{product['name']}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"Цена: <b>{price_fmt} ₽</b>   {stock_text}\n"
    )
    if product["description"]:
        # Telegram caption limit is 1024 chars — trim if needed
        desc = product["description"]
        available = 1024 - len(caption) - 2
        if len(desc) > available:
            desc = desc[:available - 1] + "…"
        caption += f"\n{desc}"

    kb = product_detail_kb(product_id, product["category_id"] or 0)
    photos = product.get("photos") or []

    if photos:
        await safe_photo(callback, photos[0], caption, kb)
    else:
        await safe_text(callback, caption, kb)


@router.callback_query(F.data.startswith("buy_"))
async def cb_buy(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    contact_info = await db.get_setting("contact_info") or "Контакты не указаны"

    price_fmt = f"{product['price']:,.0f}".replace(",", " ") if product else "—"
    name = product["name"] if product else "—"

    alert = f"{name} — {price_fmt} ₽\n\n{contact_info}"
    await callback.answer(alert, show_alert=True)
