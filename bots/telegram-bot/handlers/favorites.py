from aiogram import Router, F
from aiogram.types import CallbackQuery

import database as db
from keyboards.catalog_kb import favorites_kb
from keyboards.main_kb import back_to_menu_kb

router = Router()


@router.callback_query(F.data == "favorites")
async def cb_favorites(callback: CallbackQuery):
    await callback.answer()
    products = await db.get_user_favorites(callback.from_user.id)

    if not products:
        await _safe_text(
            callback,
            "❤️ <b>Избранное</b>\n\nВы пока не добавили ни одного товара в избранное.\n\n"
            "Нажмите «❤️ В избранное» на любом товаре, чтобы сохранить его здесь.",
            back_to_menu_kb(),
        )
        return

    await _safe_text(
        callback,
        f"❤️ <b>Избранное</b>\n\nСохранено товаров: {len(products)}",
        favorites_kb(products),
    )


@router.callback_query(F.data.startswith("fav_"))
async def cb_add_fav(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    await db.add_favorite(callback.from_user.id, product_id)
    await callback.answer("❤️ Добавлено в избранное!", show_alert=False)

    # Обновить кнопки карточки товара
    from handlers.catalog import show_product
    await show_product(callback, product_id, photo_num=0)


@router.callback_query(F.data.startswith("unfav_"))
async def cb_remove_fav(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    await db.remove_favorite(callback.from_user.id, product_id)
    await callback.answer("💔 Убрано из избранного", show_alert=False)

    # Обновить кнопки карточки товара
    from handlers.catalog import show_product
    await show_product(callback, product_id, photo_num=0)


async def _safe_text(callback: CallbackQuery, text: str, kb):
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
