from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from config import ADMIN_IDS
from keyboards.admin_kb import admin_settings_kb, cancel_kb
from states.forms import SetWelcome, SetContact

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.callback_query(F.data == "adm_settings")
async def cb_adm_settings(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.clear()
    welcome_text = await db.get_setting("welcome_text")
    contact_info = await db.get_setting("contact_info")
    has_photo = bool(await db.get_setting("welcome_photo"))

    text = (
        f"⚙️ <b>Настройки бота</b>\n\n"
        f"🖼 Приветственное фото: {'✅ есть' if has_photo else '❌ не задано'}\n"
        f"📝 Приветственный текст:\n<i>{welcome_text[:100]}...</i>\n\n"
        f"📞 Контакты:\n<i>{contact_info}</i>\n\n"
        f"Что изменить?"
    )
    await callback.message.edit_text(text, reply_markup=admin_settings_kb(), parse_mode="HTML")


@router.callback_query(F.data == "adm_set_photo")
async def cb_set_photo(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.set_state(SetWelcome.photo)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Убрать фото", callback_data="adm_remove_photo")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="adm_settings")],
    ])
    await callback.message.edit_text(
        "🖼 Отправьте новое приветственное фото:",
        reply_markup=kb
    )


@router.callback_query(SetWelcome.photo, F.data == "adm_remove_photo")
async def cb_remove_photo(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.clear()
    await db.set_setting("welcome_photo", "")
    await callback.message.edit_text("✅ Фото убрано.", reply_markup=admin_settings_kb())


@router.message(SetWelcome.photo, F.photo)
async def process_welcome_photo(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    file_id = message.photo[-1].file_id
    await db.set_setting("welcome_photo", file_id)
    await message.answer("✅ Приветственное фото обновлено!", reply_markup=admin_settings_kb())


@router.callback_query(F.data == "adm_set_welcome_text")
async def cb_set_welcome_text(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.set_state(SetWelcome.text)
    await callback.message.edit_text(
        "📝 Введите новый приветственный текст:",
        reply_markup=cancel_kb("adm_settings")
    )


@router.message(SetWelcome.text)
async def process_welcome_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await db.set_setting("welcome_text", message.text)
    await message.answer("✅ Приветственный текст обновлён!", reply_markup=admin_settings_kb())


@router.callback_query(F.data == "adm_set_contact")
async def cb_set_contact(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.set_state(SetContact.text)
    await callback.message.edit_text(
        "📞 Введите новые контактные данные (текст, ссылки, @username):",
        reply_markup=cancel_kb("adm_settings")
    )


@router.message(SetContact.text)
async def process_contact_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await db.set_setting("contact_info", message.text)
    await message.answer("✅ Контактная информация обновлена!", reply_markup=admin_settings_kb())


# ─── Review Management ───────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_reviews")
async def cb_adm_reviews(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    from keyboards.admin_kb import admin_reviews_kb
    pending = await db.get_pending_reviews()
    await callback.message.edit_text(
        f"⭐ <b>Управление отзывами</b>\n\n⏳ На модерации: {len(pending)}",
        reply_markup=admin_reviews_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "adm_pending_reviews")
async def cb_pending_reviews(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    reviews = await db.get_pending_reviews()

    if not reviews:
        from keyboards.admin_kb import admin_reviews_kb
        await callback.message.edit_text("✅ Нет отзывов на модерации.", reply_markup=admin_reviews_kb())
        return

    review = reviews[0]
    stars = "⭐" * review["rating"]
    username = f"@{review['username']}" if review["username"] else "Аноним"

    text = (
        f"⏳ <b>Отзыв на модерации</b> (осталось: {len(reviews)})\n\n"
        f"👤 {username}\n"
        f"{stars}\n\n"
        f"💬 {review['text']}"
    )
    from keyboards.admin_kb import review_actions_kb
    if review.get("photo_file_id"):
        try:
            await callback.message.delete()
            await callback.message.answer_photo(
                review["photo_file_id"],
                caption=text,
                reply_markup=review_actions_kb(review["id"]),
                parse_mode="HTML"
            )
        except Exception:
            await callback.message.edit_text(text, reply_markup=review_actions_kb(review["id"]), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=review_actions_kb(review["id"]), parse_mode="HTML")


@router.callback_query(F.data == "adm_approved_reviews")
async def cb_approved_reviews(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    reviews = await db.get_approved_reviews(limit=10)
    from keyboards.admin_kb import admin_reviews_kb

    if not reviews:
        await callback.message.edit_text("📭 Нет одобренных отзывов.", reply_markup=admin_reviews_kb())
        return

    text = "✅ <b>Одобренные отзывы:</b>\n\n"
    for rev in reviews:
        stars = "⭐" * rev["rating"]
        username = f"@{rev['username']}" if rev["username"] else "Аноним"
        text += f"{stars} {username}: {rev['text'][:80]}...\n\n"

    await callback.message.edit_text(text, reply_markup=admin_reviews_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("adm_approve_rev_"))
async def cb_approve_review(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer("✅ Одобрено!")
    review_id = int(callback.data.split("_")[3])
    await db.approve_review(review_id)
    # show next pending
    await cb_pending_reviews(callback)


@router.callback_query(F.data.startswith("adm_del_rev_"))
async def cb_del_review(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer("🗑 Удалено!")
    review_id = int(callback.data.split("_")[3])
    await db.delete_review(review_id)
    await cb_pending_reviews(callback)
