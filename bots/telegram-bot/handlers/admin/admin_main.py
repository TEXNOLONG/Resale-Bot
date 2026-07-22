import os
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

import database as db
from config import ADMIN_IDS
from keyboards.admin_kb import admin_main_kb, admin_orders_kb
from utils import safe_edit_text

router = Router()
logger = logging.getLogger(__name__)

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "bot.log")


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    await state.clear()
    await _send_admin_menu(message)


async def _send_admin_menu(message: Message):
    users    = await db.get_users_count()
    products = await db.get_all_products(include_out_of_stock=True)
    pending  = await db.get_pending_reviews()
    orders   = await db.get_orders_count()
    admin_photo = await db.get_setting("admin_photo")

    text = (
        f"🔧 <b>Панель администратора</b>\n\n"
        f"👥 Пользователей: {users}\n"
        f"📦 Товаров: {len(products)}\n"
        f"🛒 Заказов: {orders}\n"
        f"⏳ Отзывов на модерации: {len(pending)}\n\n"
        f"Выберите раздел:"
    )
    if admin_photo:
        await message.answer_photo(admin_photo, caption=text, reply_markup=admin_main_kb(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=admin_main_kb(), parse_mode="HTML")


@router.callback_query(F.data == "adm_back")
async def cb_adm_back(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await callback.answer()
    await state.clear()

    users    = await db.get_users_count()
    products = await db.get_all_products(include_out_of_stock=True)
    pending  = await db.get_pending_reviews()
    orders   = await db.get_orders_count()
    admin_photo = await db.get_setting("admin_photo")

    text = (
        f"🔧 <b>Панель администратора</b>\n\n"
        f"👥 Пользователей: {users}\n"
        f"📦 Товаров: {len(products)}\n"
        f"🛒 Заказов: {orders}\n"
        f"⏳ Отзывов на модерации: {len(pending)}\n\n"
        f"Выберите раздел:"
    )
    if admin_photo:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(admin_photo, caption=text, reply_markup=admin_main_kb(), parse_mode="HTML")
    else:
        try:
            await safe_edit_text(callback.message, text, reply_markup=admin_main_kb(), parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=admin_main_kb(), parse_mode="HTML")


# ─── Заказы ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_orders")
async def cb_adm_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    orders = await db.get_orders_count()
    await safe_edit_text(callback.message, 
        f"🛒 <b>Заказы</b>\n\nВсего заказов: {orders}",
        reply_markup=admin_orders_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "adm_list_orders")
async def cb_list_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    orders = await db.get_orders(limit=20)

    if not orders:
        await safe_edit_text(callback.message, "📭 Заказов пока нет.", reply_markup=admin_orders_kb())
        return

    text = "🛒 <b>Последние заказы</b>\n\n"
    for o in orders:
        username = f"@{o['username']}" if o["username"] else o["first_name"] or "Покупатель"
        date = o["created_at"].strftime("%d.%m %H:%M")
        price_fmt = f"{o['product_price']:,.0f}".replace(",", " ")
        text += (
            f"#{o['id']} · {date}\n"
            f"👤 {username}  (ID: {o['user_id']})\n"
            f"📦 {o['product_name']} — {price_fmt} ₽\n"
        )
        if o["comment"]:
            text += f"💬 {o['comment'][:60]}\n"
        text += "\n"

    if len(text) > 4000:
        text = text[:4000] + "…"

    await safe_edit_text(callback.message, text, reply_markup=admin_orders_kb(), parse_mode="HTML")


# ─── Логи ─────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_logs")
async def cb_adm_logs(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()

    if not os.path.exists(LOG_FILE):
        await callback.message.answer("📋 Лог-файл пока пуст или не создан.")
        return

    size = os.path.getsize(LOG_FILE)
    if size == 0:
        await callback.message.answer("📋 Лог-файл пуст.")
        return

    # Если файл большой — отправляем весь; Telegram принимает до 50 МБ
    try:
        log_input = FSInputFile(LOG_FILE, filename="bot.log")
        await callback.message.answer_document(
            log_input,
            caption=f"📋 <b>Лог бота</b>\n\nРазмер: {size // 1024} КБ",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке лога: {e}")
        await callback.message.answer(f"❌ Не удалось отправить лог: {e}")
