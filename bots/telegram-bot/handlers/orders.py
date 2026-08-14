import logging
from html import escape

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

import database as db
from config import ADMIN_IDS
from keyboards.main_kb import back_to_menu_kb
from states.forms import PlaceOrder, AdminReply

router = Router()
logger = logging.getLogger(__name__)


# ─── Начало оформления заказа ────────────────────────────────────────────────

@router.callback_query(F.data.regexp(r'^order_\d+$'))
async def cb_order_start(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)

    if not product:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    await callback.answer()
    price_fmt = f"{product['price']:,.0f}".replace(",", " ")
    product_name = escape(str(product["name"]))
    await state.update_data(product_id=product_id,
                            product_name=product["name"],
                            product_price=float(product["price"]))
    await state.set_state(PlaceOrder.comment)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Пропустить", callback_data="order_skip_comment")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"prod_{product_id}")],
    ])
    await callback.message.answer(
        f"🛒 <b>Оформление заказа</b>\n\n"
        f"📦 {product_name}\n"
        f"💰 {price_fmt} ₽\n\n"
        f"Оставьте комментарий к заказу\n"
        f"<i>(размер, цвет, способ связи и т.д.)</i>\n\n"
        f"Или нажмите «Пропустить»:",
        reply_markup=kb,
        parse_mode="HTML"
    )


# ─── Комментарий пользователя ────────────────────────────────────────────────

@router.message(PlaceOrder.comment, F.text)
async def process_order_comment(message: Message, state: FSMContext):
    comment = message.text.strip()
    await state.update_data(comment=comment)
    await _show_confirm(message, state)


@router.message(PlaceOrder.comment)
async def process_invalid_order_comment(message: Message):
    await message.answer("Пожалуйста, отправьте комментарий текстом или нажмите «Пропустить».")


@router.callback_query(PlaceOrder.comment, F.data == "order_skip_comment")
async def cb_skip_comment(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(comment="")
    await _show_confirm(callback.message, state, edit=False)


async def _show_confirm(message: Message, state: FSMContext, edit: bool = False):
    data = await state.get_data()
    product_name = escape(str(data.get("product_name", "—")))
    product_price = data.get("product_price", 0)
    comment = data.get("comment", "")
    price_fmt = f"{product_price:,.0f}".replace(",", " ")

    text = (
        f"✅ <b>Подтвердить заказ?</b>\n\n"
        f"📦 {product_name}\n"
        f"💰 {price_fmt} ₽\n"
    )
    if comment:
        text += f"\n💬 Комментарий: {escape(str(comment))}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="order_confirm"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu"),
        ]
    ])
    if edit:
        await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


# ─── Подтверждение заказа ────────────────────────────────────────────────────

@router.callback_query(PlaceOrder.comment, F.data == "order_confirm")
@router.callback_query(F.data == "order_confirm")
async def cb_order_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    if not data:
        await callback.message.edit_text("Сессия устарела. Начните заново.", reply_markup=back_to_menu_kb())
        return

    user = callback.from_user
    product_id   = data.get("product_id")
    product_name = data.get("product_name", "—")
    product_price = data.get("product_price", 0)
    comment      = data.get("comment", "")

    await state.clear()

    order_id = await db.create_order(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        product_id=product_id,
        product_name=product_name,
        product_price=product_price,
        comment=comment,
    )

    price_fmt = f"{product_price:,.0f}".replace(",", " ")
    await callback.message.edit_text(
        f"✅ <b>Заявка #{order_id} отправлена!</b>\n\n"
        f"Мы свяжемся с вами в ближайшее время.\n"
        f"Если хотите ускорить — напишите напрямую через раздел «Контакты».",
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML"
    )

    # Уведомление всем администраторам
    username_str = (
        f"@{escape(user.username)}"
        if user.username
        else escape(user.first_name or "Покупатель")
    )
    admin_text = (
        f"🛒 <b>Новый заказ #{order_id}</b>\n\n"
        f"👤 {username_str}  (ID: <code>{user.id}</code>)\n"
        f"🔗 tg://user?id={user.id}\n\n"
        f"📦 {escape(str(product_name))}\n"
        f"💰 {price_fmt} ₽\n"
    )
    if comment:
        admin_text += f"\n💬 <i>{escape(str(comment))}</i>"

    from keyboards.admin_kb import order_reply_kb
    for admin_id in ADMIN_IDS:
        try:
            await callback.bot.send_message(
                admin_id,
                admin_text,
                reply_markup=order_reply_kb(order_id, user.id),
                parse_mode="HTML"
            )
        except Exception:
            logger.exception("Не удалось отправить уведомление администратору")


# ─── Ответ администратора покупателю ─────────────────────────────────────────

@router.callback_query(F.data.startswith("adm_reply_"))
async def cb_adm_reply_start(callback: CallbackQuery, state: FSMContext):
    from config import ADMIN_IDS
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.answer()

    parts = callback.data.split("_")   # adm_reply_<order_id>_<user_id>
    order_id = int(parts[2])
    user_id  = int(parts[3])

    await state.update_data(reply_order_id=order_id, reply_user_id=user_id)
    await state.set_state(AdminReply.message)

    order = await db.get_order(order_id)
    product_name = escape(str(order["product_name"])) if order else "—"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="adm_back")]
    ])
    await callback.message.answer(
        f"✉️ <b>Написать покупателю по заказу #{order_id}</b>\n"
        f"<i>{product_name}</i>\n\n"
        f"Введите ваше сообщение:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(AdminReply.message)
async def process_admin_reply(message: Message, state: FSMContext):
    from config import ADMIN_IDS
    if message.from_user.id not in ADMIN_IDS:
        return

    data = await state.get_data()
    order_id = data.get("reply_order_id")
    user_id  = data.get("reply_user_id")
    await state.clear()

    if not user_id:
        await message.answer("Ошибка: не найден покупатель.")
        return

    reply_text = (
        f"✉️ <b>Сообщение от магазина</b> (заказ #{order_id})\n\n"
        f"{escape(message.text or '')}"
    )
    try:
        await message.bot.send_message(user_id, reply_text, parse_mode="HTML")
        await message.answer(f"✅ Сообщение отправлено покупателю (заказ #{order_id}).")
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить: {e}")
