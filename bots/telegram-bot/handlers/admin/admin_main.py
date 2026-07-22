from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from config import ADMIN_IDS
from keyboards.admin_kb import admin_main_kb

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    await state.clear()
    users = await db.get_users_count()
    products = await db.get_all_products(include_out_of_stock=True)
    reviews_pending = await db.get_pending_reviews()

    text = (
        f"🔧 <b>Панель администратора</b>\n\n"
        f"👥 Пользователей: {users}\n"
        f"📦 Товаров: {len(products)}\n"
        f"⏳ Отзывов на модерации: {len(reviews_pending)}\n\n"
        f"Выберите раздел:"
    )
    await message.answer(text, reply_markup=admin_main_kb(), parse_mode="HTML")


@router.callback_query(F.data == "adm_back")
async def cb_adm_back(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await callback.answer()
    await state.clear()

    users = await db.get_users_count()
    products = await db.get_all_products(include_out_of_stock=True)
    reviews_pending = await db.get_pending_reviews()

    text = (
        f"🔧 <b>Панель администратора</b>\n\n"
        f"👥 Пользователей: {users}\n"
        f"📦 Товаров: {len(products)}\n"
        f"⏳ Отзывов на модерации: {len(reviews_pending)}\n\n"
        f"Выберите раздел:"
    )
    try:
        await callback.message.edit_text(text, reply_markup=admin_main_kb(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=admin_main_kb(), parse_mode="HTML")
