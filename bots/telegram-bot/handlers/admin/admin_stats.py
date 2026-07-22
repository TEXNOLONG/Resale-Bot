from aiogram import Router, F
from aiogram.types import CallbackQuery

import database as db
from config import ADMIN_IDS
from keyboards.admin_kb import back_to_admin_kb

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.callback_query(F.data == "adm_stats")
async def cb_adm_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()

    users_total = await db.get_users_count()
    users_today = await db.get_new_users_today()
    total_clicks = await db.get_total_clicks()
    reviews_count = await db.get_reviews_count()
    top_views = await db.get_top_products(5)
    top_clicks = await db.get_top_clicked_products(5)

    text = (
        f"📊 <b>Статистика магазина</b>\n\n"
        f"👥 <b>Пользователи</b>\n"
        f"Всего: {users_total}\n"
        f"Новых сегодня: {users_today}\n\n"
        f"🖱 <b>Активность</b>\n"
        f"Всего кликов по товарам: {total_clicks}\n"
        f"Одобренных отзывов: {reviews_count}\n\n"
    )

    if top_views:
        text += "👁 <b>Топ по просмотрам:</b>\n"
        for i, p in enumerate(top_views, 1):
            stock = "✅" if p["in_stock"] else "❌"
            text += f"{i}. {stock} {p['name']} — {p['views']} просм.\n"
        text += "\n"

    if top_clicks:
        text += "🔥 <b>Топ по кликам:</b>\n"
        for i, p in enumerate(top_clicks, 1):
            text += f"{i}. {p['name']} — {p['clicks']} кликов\n"

    await callback.message.edit_text(text, reply_markup=back_to_admin_kb(), parse_mode="HTML")
