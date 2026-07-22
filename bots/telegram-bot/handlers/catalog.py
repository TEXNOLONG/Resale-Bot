from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.utils.media_group import MediaGroupBuilder

import database as db
from keyboards.catalog_kb import (
    categories_kb, products_list_kb, product_detail_kb, buy_kb
)

router = Router()


@router.callback_query(F.data == "catalog")
async def cb_catalog(callback: CallbackQuery):
    await callback.answer()
    categories = await db.get_categories()
    if not categories:
        from keyboards.main_kb import back_to_menu_kb
        await callback.message.edit_text(
            "😔 Категорий пока нет. Загляните позже!",
            reply_markup=back_to_menu_kb()
        )
        return

    await callback.message.edit_text(
        "🗂 <b>Каталог товаров</b>\n\nВыберите категорию:",
        reply_markup=categories_kb(categories),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("cat_"))
async def cb_category(callback: CallbackQuery):
    await callback.answer()
    category_id = int(callback.data.split("_")[1])
    category = await db.get_category(category_id)
    products = await db.get_products_by_category(category_id)

    if not products:
        categories = await db.get_categories()
        await callback.message.edit_text(
            f"😔 В категории <b>{category['name']}</b> пока нет товаров.",
            reply_markup=categories_kb(categories),
            parse_mode="HTML"
        )
        return

    cat_name = f"{category['emoji']} {category['name']}" if category else "Категория"
    await callback.message.edit_text(
        f"<b>{cat_name}</b>\n\nДоступно товаров: {len(products)}\nВыберите товар:",
        reply_markup=products_list_kb(products, category_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("prod_"))
async def cb_product(callback: CallbackQuery):
    await callback.answer()
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)

    if not product:
        await callback.message.edit_text("❌ Товар не найден.")
        return

    await db.increment_views(product_id)
    await db.add_product_click(product_id, callback.from_user.id)

    stock_text = "✅ В наличии" if product["in_stock"] else "❌ Нет в наличии"
    cat_name = product.get("cat_name") or "Без категории"

    text = (
        f"📦 <b>{product['name']}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🗂 Категория: {cat_name}\n"
        f"💰 Цена: <b>{product['price']:,.0f} ₽</b>\n"
        f"📊 Статус: {stock_text}\n"
    )
    if product["description"]:
        text += f"\n📝 <b>Описание:</b>\n{product['description']}"

    kb = product_detail_kb(product_id, product["category_id"] or 0)

    photos = product.get("photos") or []
    if photos and len(photos) == 1:
        try:
            await callback.message.delete()
            await callback.message.answer_photo(
                photos[0],
                caption=text,
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    elif photos and len(photos) > 1:
        try:
            await callback.message.delete()
            media_group = MediaGroupBuilder()
            for i, photo in enumerate(photos[:10]):
                media_group.add_photo(media=photo, caption=text if i == 0 else None, parse_mode="HTML" if i == 0 else None)
            await callback.message.answer_media_group(media=media_group.build())
            await callback.message.answer("⬆️ Фото товара выше", reply_markup=kb)
        except Exception:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("buy_"))
async def cb_buy(callback: CallbackQuery):
    await callback.answer()
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)

    if not product:
        return

    contact_info = await db.get_setting("contact_info")
    text = (
        f"🛒 <b>Оформление заказа</b>\n\n"
        f"Товар: <b>{product['name']}</b>\n"
        f"Цена: <b>{product['price']:,.0f} ₽</b>\n\n"
        f"Для оформления заказа свяжитесь с нами:\n{contact_info}"
    )

    kb = buy_kb(product_id)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
