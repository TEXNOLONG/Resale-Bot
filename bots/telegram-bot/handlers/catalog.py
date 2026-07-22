from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto

import database as db
from photos import get_all_product_photos
from keyboards.catalog_kb import (
    categories_kb, products_list_kb, product_detail_kb
)

router = Router()


# ─── helpers ──────────────────────────────────────────────────────────────────

async def safe_text(callback: CallbackQuery, text: str, kb):
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")


async def _send_photo(callback: CallbackQuery, photo_type: str, photo_src: str, caption: str, kb):
    """Удаляет текущее сообщение и шлёт новое с фото."""
    try:
        await callback.message.delete()
    except Exception:
        pass
    if photo_type == "file":
        await callback.message.answer_photo(
            FSInputFile(photo_src), caption=caption, reply_markup=kb, parse_mode="HTML"
        )
    else:
        await callback.message.answer_photo(
            photo_src, caption=caption, reply_markup=kb, parse_mode="HTML"
        )


async def _edit_photo(callback: CallbackQuery, photo_type: str, photo_src: str, caption: str, kb):
    """Редактирует фото в сообщении без удаления (edit_media). Fallback — удалить и переслать."""
    if photo_type == "file":
        media = InputMediaPhoto(media=FSInputFile(photo_src), caption=caption, parse_mode="HTML")
    else:
        media = InputMediaPhoto(media=photo_src, caption=caption, parse_mode="HTML")
    try:
        await callback.message.edit_media(media, reply_markup=kb)
    except Exception:
        # Fallback: удалить и переслать
        try:
            await callback.message.delete()
        except Exception:
            pass
        if photo_type == "file":
            await callback.message.answer_photo(
                FSInputFile(photo_src), caption=caption, reply_markup=kb, parse_mode="HTML"
            )
        else:
            await callback.message.answer_photo(
                photo_src, caption=caption, reply_markup=kb, parse_mode="HTML"
            )


# ─── show product ─────────────────────────────────────────────────────────────

async def show_product(callback: CallbackQuery, product_id: int, photo_num: int = 0):
    product = await db.get_product(product_id)
    if not product:
        await safe_text(callback, "Товар не найден.", None)
        return

    await db.increment_views(product_id)
    await db.add_product_click(product_id, callback.from_user.id)

    photos = get_all_product_photos(dict(product))
    total = len(photos)
    photo_num = max(0, min(photo_num, total - 1)) if total > 0 else 0

    is_fav = await db.is_favorite(callback.from_user.id, product_id)

    stock_text = "В наличии ✓" if product["in_stock"] else "Нет в наличии"
    price_fmt = f"{product['price']:,.0f}".replace(",", " ")

    caption = (
        f"<b>{product['name']}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"Цена: <b>{price_fmt} ₽</b>   {stock_text}\n"
    )
    if product["description"]:
        desc = product["description"]
        available = 1024 - len(caption) - 2
        if len(desc) > available:
            desc = desc[: available - 1] + "…"
        caption += f"\n{desc}"

    kb = product_detail_kb(
        product_id,
        product["category_id"] or 0,
        photo_num,
        total,
        is_fav,
    )

    if photos:
        photo_type, photo_src = photos[photo_num]
        if getattr(callback, '_use_edit_media', False):
            await _edit_photo(callback, photo_type, photo_src, caption, kb)
        else:
            await _send_photo(callback, photo_type, photo_src, caption, kb)
    else:
        await safe_text(callback, caption, kb)


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
            categories_kb(categories),
        )
        return

    cat_name = f"{category['emoji']} {category['name']}" if category else "Категория"
    await safe_text(
        callback,
        f"<b>{cat_name}</b>\n\nТоваров: {len(products)}",
        products_list_kb(products, category_id),
    )


@router.callback_query(F.data.startswith("prod_"))
async def cb_product(callback: CallbackQuery):
    await callback.answer()
    product_id = int(callback.data.split("_")[1])
    await show_product(callback, product_id, photo_num=0)


@router.callback_query(F.data.startswith("prodphoto_"))
async def cb_prodphoto(callback: CallbackQuery):
    await callback.answer()
    parts = callback.data.split("_")
    product_id = int(parts[1])
    photo_num = int(parts[2])
    # Свайп — редактируем фото на месте без удаления сообщения
    callback._use_edit_media = True
    await show_product(callback, product_id, photo_num=photo_num)
