from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from keyboards.main_kb import main_menu_kb

router = Router()


async def send_main_menu(message: Message, edit: bool = False):
    welcome_text = await db.get_setting("welcome_text")
    welcome_photo = await db.get_setting("welcome_photo")

    if not welcome_text:
        welcome_text = "Добро пожаловать! 🛍️\nВыберите нужный раздел:"

    kb = main_menu_kb()

    if welcome_photo:
        if edit:
            try:
                await message.edit_text(welcome_text, reply_markup=kb)
            except Exception:
                await message.answer_photo(welcome_photo, caption=welcome_text, reply_markup=kb)
        else:
            await message.answer_photo(welcome_photo, caption=welcome_text, reply_markup=kb)
    else:
        if edit:
            try:
                await message.edit_text(welcome_text, reply_markup=kb)
            except Exception:
                await message.answer(welcome_text, reply_markup=kb)
        else:
            await message.answer(welcome_text, reply_markup=kb)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await db.upsert_user(
        user.id,
        user.username or "",
        user.first_name or "",
        user.last_name or ""
    )
    await send_main_menu(message)


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await send_main_menu(callback.message, edit=True)


@router.callback_query(F.data == "contacts")
async def cb_contacts(callback: CallbackQuery):
    await callback.answer()
    contact_info = await db.get_setting("contact_info")
    if not contact_info:
        contact_info = "Контакты не указаны"

    from keyboards.main_kb import back_to_menu_kb
    await callback.message.edit_text(
        f"📞 <b>Контакты</b>\n\n{contact_info}",
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML"
    )
