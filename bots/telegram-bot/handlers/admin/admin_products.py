import os
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from config import ADMIN_IDS
from photos import ensure_product_photo_folder, next_photo_number
from keyboards.admin_kb import (
    admin_products_kb, categories_select_kb, products_select_kb,
    edit_product_fields_kb, back_to_admin_kb, cancel_kb, confirm_delete_kb
)
from states.forms import AddProduct, EditProduct

router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ─── Product List ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_products")
async def cb_adm_products(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "📦 <b>Управление товарами</b>\n\nВыберите действие:",
        reply_markup=admin_products_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "adm_list_products")
async def cb_adm_list_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    products = await db.get_all_products(include_out_of_stock=True)
    if not products:
        await callback.message.edit_text("📦 Товаров пока нет.", reply_markup=admin_products_kb())
        return

    text = "📦 <b>Все товары</b>\n\n"
    for p in products[:30]:
        stock = "✅" if p["in_stock"] else "❌"
        cat   = p.get("cat_name") or "Без категории"
        text += f"{stock} <b>{p['name']}</b>\n   💰 {p['price']:,.0f} ₽ | 📁 {cat} | 👁 {p['views']}\n\n"

    await callback.message.edit_text(text, reply_markup=admin_products_kb(), parse_mode="HTML")


# ─── Add Product ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_add_product")
async def cb_adm_add_product(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    categories = await db.get_categories()
    if not categories:
        await callback.message.edit_text("❌ Сначала добавьте категорию!", reply_markup=back_to_admin_kb())
        return
    await state.set_state(AddProduct.category)
    await callback.message.edit_text(
        "➕ <b>Добавление товара</b>\n\nВыберите категорию:",
        reply_markup=categories_select_kb(categories, prefix="adm_selcat"),
        parse_mode="HTML"
    )


@router.callback_query(AddProduct.category, F.data.startswith("adm_selcat_"))
async def cb_adm_selcat(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    category_id = int(callback.data.split("_")[2])
    await state.update_data(category_id=category_id)
    await state.set_state(AddProduct.name)
    await callback.message.edit_text(
        "📝 Введите <b>название</b> товара:",
        reply_markup=cancel_kb("adm_products"),
        parse_mode="HTML"
    )


@router.message(AddProduct.name)
async def process_product_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AddProduct.description)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Пропустить", callback_data="adm_skip_desc")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="adm_products")],
    ])
    await message.answer("📄 Введите <b>описание</b> товара (или пропустите):", reply_markup=kb, parse_mode="HTML")


@router.callback_query(AddProduct.description, F.data == "adm_skip_desc")
async def cb_skip_desc(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.update_data(description="")
    await state.set_state(AddProduct.price)
    await callback.message.edit_text(
        "💰 Введите <b>цену</b> товара (например: 5990):",
        reply_markup=cancel_kb("adm_products"),
        parse_mode="HTML"
    )


@router.message(AddProduct.description)
async def process_product_desc(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(AddProduct.price)
    await message.answer(
        "💰 Введите <b>цену</b> товара (например: 5990):",
        reply_markup=cancel_kb("adm_products"),
        parse_mode="HTML"
    )


@router.message(AddProduct.price)
async def process_product_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        price = float(message.text.strip().replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.answer("❌ Введите корректную цену (число):")
        return
    await state.update_data(price=price, photo_count=0)
    await state.set_state(AddProduct.photos)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Без фото", callback_data="adm_skip_photos")],
        [InlineKeyboardButton(text="✅ Готово", callback_data="adm_done_photos")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="adm_products")],
    ])
    await message.answer(
        "📸 Отправьте фото товара (можно несколько по одному).\n"
        "Фото будут сохранены в папке и пронумерованы автоматически.\n\n"
        "Затем нажмите «Готово»:",
        reply_markup=kb
    )


@router.message(AddProduct.photos, F.photo)
async def process_product_photo(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    product_id_tmp = data.get("tmp_product_id")

    # Создаём временную запись в БД если ещё нет, чтобы знать ID для папки
    # Вместо этого используем временный счётчик и сохраним всё в конце
    photo_count = data.get("photo_count", 0)
    pending_photos = data.get("pending_photos", [])

    # Скачиваем фото в память (file_id) — реальная папка создастся после сохранения товара
    file_id = message.photo[-1].file_id
    pending_photos.append(file_id)
    photo_count += 1
    await state.update_data(pending_photos=pending_photos, photo_count=photo_count)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Готово", callback_data="adm_done_photos")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="adm_products")],
    ])
    await message.answer(f"📸 Фото {photo_count} добавлено. Можно ещё или нажмите «Готово».", reply_markup=kb)


@router.callback_query(AddProduct.photos, F.data.in_({"adm_skip_photos", "adm_done_photos"}))
async def cb_finish_photos(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    data = await state.get_data()
    await state.clear()

    pending_photos = data.get("pending_photos", [])

    product_id = await db.add_product(
        data.get("category_id"),
        data.get("name"),
        data.get("description", ""),
        data.get("price"),
        photos=[],
        photo_folder="",
    )

    # Скачиваем фото в папку продукта
    if pending_photos:
        folder = ensure_product_photo_folder(product_id)
        for i, file_id in enumerate(pending_photos, start=1):
            try:
                file = await callback.bot.get_file(file_id)
                ext  = file.file_path.rsplit(".", 1)[-1] if "." in file.file_path else "jpg"
                dest = os.path.join(folder, f"{i}.{ext}")
                await callback.bot.download_file(file.file_path, destination=dest)
                logger.info(f"Сохранено фото товара #{product_id}: {dest}")
            except Exception as e:
                logger.error(f"Ошибка скачивания фото: {e}")

    await callback.message.edit_text(
        f"✅ <b>Товар добавлен!</b>\n\nID: {product_id}\nНазвание: {data.get('name')}\n"
        f"Цена: {data.get('price'):,.0f} ₽\nФото: {len(pending_photos)} шт.",
        reply_markup=admin_products_kb(),
        parse_mode="HTML"
    )


# ─── Edit Product ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_edit_product")
async def cb_adm_edit_product(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    products = await db.get_all_products(include_out_of_stock=True)
    if not products:
        await callback.message.edit_text("📦 Нет товаров для редактирования.", reply_markup=admin_products_kb())
        return
    await state.set_state(EditProduct.select)
    await callback.message.edit_text(
        "✏️ <b>Выберите товар для редактирования:</b>",
        reply_markup=products_select_kb(products, "adm_editprod"),
        parse_mode="HTML"
    )


@router.callback_query(EditProduct.select, F.data.startswith("adm_editprod_"))
async def cb_select_edit_product(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    product_id = int(callback.data.split("_")[2])
    product    = await db.get_product(product_id)
    await state.update_data(product_id=product_id)
    await state.set_state(EditProduct.field)

    stock = "✅ В наличии" if product["in_stock"] else "❌ Нет в наличии"
    folder = product.get("photo_folder") or "—"
    text = (
        f"✏️ <b>{product['name']}</b>\n"
        f"Цена: {product['price']:,.0f} ₽\n"
        f"Статус: {stock}\n"
        f"📁 Папка фото: {folder}\n\n"
        f"Что изменить?"
    )
    await callback.message.edit_text(text, reply_markup=edit_product_fields_kb(product_id), parse_mode="HTML")


@router.callback_query(EditProduct.field, F.data.startswith("adm_edit_name_"))
async def cb_edit_name(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.update_data(field="name")
    await state.set_state(EditProduct.value)
    await callback.message.edit_text("📝 Введите новое название:", reply_markup=cancel_kb("adm_products"))


@router.callback_query(EditProduct.field, F.data.startswith("adm_edit_desc_"))
async def cb_edit_desc(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.update_data(field="description")
    await state.set_state(EditProduct.value)
    await callback.message.edit_text("📄 Введите новое описание:", reply_markup=cancel_kb("adm_products"))


@router.callback_query(EditProduct.field, F.data.startswith("adm_edit_price_"))
async def cb_edit_price(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    await state.update_data(field="price")
    await state.set_state(EditProduct.value)
    await callback.message.edit_text("💰 Введите новую цену (число):", reply_markup=cancel_kb("adm_products"))


@router.callback_query(EditProduct.field, F.data.startswith("adm_edit_folder_"))
async def cb_edit_folder(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    product_id = int(callback.data.split("_")[3])
    await state.update_data(field="photo_folder", product_id=product_id)
    await state.set_state(EditProduct.value)
    from photos import PRODUCT_PHOTOS_DIR, SEED_PHOTOS_DIR
    await callback.message.edit_text(
        "📁 Введите путь к папке с фото товара.\n\n"
        f"Папки товаров: <code>{PRODUCT_PHOTOS_DIR}/prod_&lt;id&gt;/</code>\n"
        f"Seed-фото: <code>{SEED_PHOTOS_DIR}/&lt;папка&gt;/</code>\n\n"
        "Файлы в папке должны называться: <code>1.jpg</code>, <code>2.png</code> и т.д.",
        reply_markup=cancel_kb("adm_products"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_toggle_stock_"))
async def cb_toggle_stock(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    product_id = int(callback.data.split("_")[3])
    product    = await db.get_product(product_id)
    new_stock  = not product["in_stock"]
    await db.update_product(product_id, "in_stock", new_stock)
    status = "✅ В наличии" if new_stock else "❌ Нет в наличии"
    await state.clear()
    await callback.message.edit_text(
        f"🔄 Статус <b>{product['name']}</b> изменён: {status}",
        reply_markup=admin_products_kb(),
        parse_mode="HTML"
    )


@router.message(EditProduct.value)
async def process_edit_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data       = await state.get_data()
    field      = data.get("field")
    product_id = data.get("product_id")
    value      = message.text.strip()

    if field == "price":
        try:
            value = float(value.replace(",", ".").replace(" ", ""))
        except ValueError:
            await message.answer("❌ Введите корректную цену:")
            return

    if field == "photo_folder":
        if not os.path.isdir(value):
            await message.answer(f"❌ Папка не найдена: <code>{value}</code>\nПроверьте путь.", parse_mode="HTML")
            return

    await db.update_product(product_id, field, value)
    await state.clear()

    field_names = {
        "name": "Название", "description": "Описание",
        "price": "Цена", "photo_folder": "Папка с фото"
    }
    await message.answer(
        f"✅ <b>{field_names.get(field, field)}</b> обновлено!",
        reply_markup=admin_products_kb(),
        parse_mode="HTML"
    )


# ─── Delete Product ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm_del_product")
async def cb_adm_del_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    products = await db.get_all_products(include_out_of_stock=True)
    if not products:
        await callback.message.edit_text("📦 Нет товаров для удаления.", reply_markup=admin_products_kb())
        return
    await callback.message.edit_text(
        "🗑 <b>Выберите товар для удаления:</b>",
        reply_markup=products_select_kb(products, "adm_delprod"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_delprod_"))
async def cb_select_del_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    product_id = int(callback.data.split("_")[2])
    product    = await db.get_product(product_id)
    await callback.message.edit_text(
        f"⚠️ Удалить товар <b>{product['name']}</b>?\nЦена: {product['price']:,.0f} ₽",
        reply_markup=confirm_delete_kb(product_id, "prod"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("adm_confirm_del_prod_"))
async def cb_confirm_del_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer()
    product_id = int(callback.data.split("_")[4])
    await db.delete_product(product_id)
    await callback.message.edit_text("✅ Товар удалён.", reply_markup=admin_products_kb())
