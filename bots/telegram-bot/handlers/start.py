from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from keyboards.main_kb import main_menu_kb, back_to_menu_kb
from utils import safe_edit_text

router = Router()


async def send_main_menu(message: Message, edit: bool = False):
    welcome_text = await db.get_setting("welcome_text")
    welcome_photo = await db.get_setting("welcome_photo")

    if not welcome_text:
        welcome_text = "Привет! Выберите нужный раздел:"

    kb = main_menu_kb()

    if welcome_photo:
        # Всегда удаляем старое сообщение и отправляем новое с фото
        if edit:
            try:
                await message.delete()
            except Exception:
                pass
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
    text = f"<b>Контакты</b>\n\n{contact_info}"
    try:
        await safe_edit_text(callback.message, text, reply_markup=back_to_menu_kb(), parse_mode="HTML")
    except Exception:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text, reply_markup=back_to_menu_kb(), parse_mode="HTML")


@router.callback_query(F.data == "about_us")
async def cb_about_us(callback: CallbackQuery):
    await callback.answer()
    about_text = await db.get_setting("about_us_text")
    about_photo = await db.get_setting("about_us_photo")
    if not about_text:
        about_text = (
            "Мы — магазин качественной одежды и аксессуаров.\n\n"
            "Чтобы добавить текст «О нас», перейдите в Настройки в панели администратора."
        )
    full_text = f"ℹ️ <b>О нас</b>\n\n{about_text}"
    if about_photo:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(
            about_photo,
            caption=full_text,
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML"
        )
    else:
        await safe_edit_text(callback.message, 
            full_text,
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()
