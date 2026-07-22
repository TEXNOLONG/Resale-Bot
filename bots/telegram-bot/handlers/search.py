from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from keyboards.catalog_kb import search_results_kb
from keyboards.main_kb import back_to_menu_kb
from states.forms import SearchProduct

router = Router()


@router.callback_query(F.data == "search")
async def cb_search(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(SearchProduct.query)
    from keyboards.admin_kb import cancel_kb
    await callback.message.edit_text(
        "<b>Поиск</b>\n\nВведите название или ключевое слово:",
        reply_markup=cancel_kb(back_cb="main_menu"),
        parse_mode="HTML"
    )


@router.message(SearchProduct.query)
async def process_search(message: Message, state: FSMContext):
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("Введите хотя бы 2 символа.")
        return

    await state.clear()
    products = await db.search_products(query)

    if not products:
        await message.answer(
            f"По запросу «<b>{query}</b>» ничего не нашлось.\n\nПопробуйте другое слово.",
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"<b>Результаты по «{query}»</b>\n\nНайдено: {len(products)}:",
        reply_markup=search_results_kb(products),
        parse_mode="HTML"
    )
