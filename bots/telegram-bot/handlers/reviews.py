from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from keyboards.main_kb import back_to_menu_kb
from states.forms import AddReview

router = Router()

STARS = {1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐", 4: "⭐⭐⭐⭐", 5: "⭐⭐⭐⭐⭐"}


def rating_kb():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐", callback_data="rate_1"),
            InlineKeyboardButton(text="⭐⭐", callback_data="rate_2"),
            InlineKeyboardButton(text="⭐⭐⭐", callback_data="rate_3"),
        ],
        [
            InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rate_4"),
            InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rate_5"),
        ],
        [InlineKeyboardButton(text="Отмена", callback_data="main_menu")],
    ])


def reviews_menu_kb(page: int = 0, total: int = 0):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀", callback_data=f"reviews_page_{page-1}"))
    if (page + 1) * 5 < total:
        nav.append(InlineKeyboardButton(text="▶", callback_data=f"reviews_page_{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="Написать отзыв", callback_data="add_review")])
    buttons.append([InlineKeyboardButton(text="← Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "reviews")
async def cb_reviews(callback: CallbackQuery):
    await callback.answer()
    await show_reviews_page(callback, 0)


@router.callback_query(F.data.startswith("reviews_page_"))
async def cb_reviews_page(callback: CallbackQuery):
    await callback.answer()
    page = int(callback.data.split("_")[-1])
    await show_reviews_page(callback, page)


async def show_reviews_page(callback: CallbackQuery, page: int):
    per_page = 5
    offset = page * per_page
    reviews = await db.get_approved_reviews(limit=per_page, offset=offset)
    total = await db.get_reviews_count()

    if not reviews and page == 0:
        await callback.message.edit_text(
            "<b>Отзывы</b>\n\nПока нет ни одного отзыва. Будьте первым!",
            reply_markup=reviews_menu_kb(0, 0),
            parse_mode="HTML"
        )
        return

    text = f"⭐ <b>Отзывы</b> (всего: {total})\n\n"
    for review in reviews:
        stars = STARS.get(review["rating"], "⭐")
        username = f"@{review['username']}" if review["username"] else "Покупатель"
        date = review["created_at"].strftime("%d.%m.%Y")
        text += f"{stars} <b>{username}</b> · {date}\n{review['text']}\n\n"

    await callback.message.edit_text(
        text.strip(),
        reply_markup=reviews_menu_kb(page, total),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "add_review")
async def cb_add_review(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AddReview.text)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="reviews")]
    ])
    await callback.message.edit_text(
        "<b>Написать отзыв</b>\n\nРасскажите о покупке:",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )


@router.message(AddReview.text)
async def process_review_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(AddReview.rating)
    await message.answer(
        "Оцените покупку:",
        reply_markup=rating_kb()
    )


@router.callback_query(AddReview.rating, F.data.startswith("rate_"))
async def process_review_rating(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    rating = int(callback.data.split("_")[1])
    await state.update_data(rating=rating)
    await state.set_state(AddReview.photo)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Без фото →", callback_data="review_no_photo")],
        [InlineKeyboardButton(text="Отмена", callback_data="reviews")],
    ])
    await callback.message.edit_text(
        "Прикрепите фото (необязательно) или пропустите:",
        reply_markup=kb
    )


@router.callback_query(AddReview.photo, F.data == "review_no_photo")
async def process_review_no_photo(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    await state.clear()

    user = callback.from_user
    await db.add_review(
        user.id,
        user.username or "",
        data["text"],
        data["rating"],
        None
    )
    await callback.message.edit_text(
        "<b>Спасибо за отзыв!</b>\n\nПоявится после проверки.",
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML"
    )


@router.message(AddReview.photo, F.photo)
async def process_review_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    photo_file_id = message.photo[-1].file_id
    user = message.from_user
    await db.add_review(
        user.id,
        user.username or "",
        data["text"],
        data["rating"],
        photo_file_id
    )
    await message.answer(
        "<b>Спасибо за отзыв!</b>\n\nПоявится после проверки.",
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML"
    )
