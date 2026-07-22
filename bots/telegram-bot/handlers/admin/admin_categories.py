from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from config import ADMIN_IDS
from keyboards.admin_kb import admin_categories_kb, categories_select_kb, cancel_kb, confirm_delete_kb
from states.forms import AddCategory
from utils import safe_edit_text

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.callback_query(F.data == "adm_categories")
async def cb_adm_categories(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.clear()
    categories = await db.get_categories()
    text = "🗂 <b>Категории</b>\n\n"
    if categories:
        for cat in categories:
            text += f"{cat['emoji']} {cat['name']}\n"
    else:
        text += "Категорий пока нет.\n"
    text += "\nВыберите действие:"
    await safe_edit_text(callback.message, text, reply_markup=admin_categories_kb(), parse_mode="HTML")


@router.callback_query(F.data == "adm_add_category")
async def cb_adm_add_category(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.set_state(AddCategory.name)
    await safe_edit_text(callback.message, 
        "➕ <b>Добавить категорию</b>\n\nВведите название:",
        reply_markup=cancel_kb("adm_categories"),
        parse_mode="HTML"
    )


@router.message(AddCategory.name)
async def process_category_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AddCategory.emoji)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👕", callback_data="cat_emoji_👕"),
            InlineKeyboardButton(text="👟", callback_data="cat_emoji_👟"),
            InlineKeyboardButton(text="💻", callback_data="cat_emoji_💻"),
        ],
        [
            InlineKeyboardButton(text="⌚", callback_data="cat_emoji_⌚"),
            InlineKeyboardButton(text="🎒", callback_data="cat_emoji_🎒"),
            InlineKeyboardButton(text="📱", callback_data="cat_emoji_📱"),
        ],
        [
            InlineKeyboardButton(text="🧥", callback_data="cat_emoji_🧥"),
            InlineKeyboardButton(text="🩳", callback_data="cat_emoji_🩳"),
            InlineKeyboardButton(text="📦", callback_data="cat_emoji_📦"),
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="adm_categories")],
    ])
    await message.answer("Выберите эмодзи для категории:", reply_markup=kb)


@router.callback_query(AddCategory.emoji, F.data.startswith("cat_emoji_"))
async def process_category_emoji(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    emoji = callback.data.replace("cat_emoji_", "")
    data = await state.get_data()
    await state.clear()

    cat_id = await db.add_category(data["name"], emoji)
    await safe_edit_text(callback.message, 
        f"✅ Категория <b>{emoji} {data['name']}</b> добавлена!",
        reply_markup=admin_categories_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "adm_del_category")
async def cb_adm_del_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    categories = await db.get_categories()
    if not categories:
        await safe_edit_text(callback.message, "🗂 Нет категорий для удаления.", reply_markup=admin_categories_kb())
        return
    await safe_edit_text(callback.message, 
        "🗑 <b>Выберите категорию для удаления:</b>",
        reply_markup=categories_select_kb(categories, prefix="adm_delcat"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_delcat_"))
async def cb_select_del_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    cat_id = int(callback.data.split("_")[2])
    cat = await db.get_category(cat_id)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"adm_confirm_del_cat_{cat_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="adm_categories"),
        ]
    ])
    await safe_edit_text(callback.message, 
        f"⚠️ Удалить категорию <b>{cat['emoji']} {cat['name']}</b>?\n\nТовары в этой категории останутся без категории.",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_confirm_del_cat_"))
async def cb_confirm_del_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    cat_id = int(callback.data.split("_")[4])
    await db.delete_category(cat_id)
    await safe_edit_text(callback.message, "✅ Категория удалена.", reply_markup=admin_categories_kb())
