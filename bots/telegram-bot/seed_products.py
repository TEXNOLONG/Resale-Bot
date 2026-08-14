"""
Скрипт для заполнения локального JSON-хранилища начальными товарами.
Запускается один раз из папки bots/telegram-bot/ (обычно не нужен:
каталог создаётся автоматически при первом старте бота).

Фото читаются с диска из папки seed_photos/ — никуда не отправляются.

Запуск:
  python3.11 seed_products.py
"""

import asyncio
import os
import database as db

# ──────────────────────────────────────────────────────────────────────────────
# ЦЕНЫ — установите нужные значения перед запуском, потом можно поменять в боте
# ──────────────────────────────────────────────────────────────────────────────
PRICES = {
    "Худи с авторским принтом":      0,  # <-- поставьте цену
    "Худи Philipp Plein":             0,
    "Худи Yohji Yamamoto":           0,
    "Лонгслив Yohji Yamamoto":       0,
    "Лонгслив Marcelo Burlon":       0,
    "Лонгслив Acne Studios Stockholm 1996": 0,
    "AirPods Pro 2":                  0,
}

BASE_DIR = os.path.dirname(__file__)
PHOTOS_DIR = os.path.join(BASE_DIR, "seed_photos")

PRODUCTS = [
    {
        "name": "Худи с авторским принтом",
        "category": "Худи",
        "description": (
            "Черное худи с художественным принтом в минималистичном стиле. "
            "Свободная посадка (oversize). Мягкая, приятная к телу ткань. "
            "Вместительный карман-кенгуру. Капюшон с двойным слоем ткани.\n\n"
            "Размеры в наличии: S, M, L, XL, 2XL\n"
            "Подбор размера (обхват груди):\n"
            "S — 88-92 см\n"
            "M — 92-96 см\n"
            "L — 96-100 см\n"
            "XL — 100-104 см\n"
            "2XL — 104-108 см\n\n"
            "Цвет: черный. Унисекс."
        ),
        "photos_dir": "1_hoodie_print",
    },
    {
        "name": "Худи Philipp Plein",
        "category": "Худи",
        "description": (
            "Плотный и мягкий хлопок, отлично держит форму. "
            "Стильный принт с яркими деталями. "
            "Свободный фасон oversize — подходит как парням, так и девушкам. "
            "Отлично сочетается с джинсами, карго, спортивными брюками и кроссовками.\n\n"
            "Размеры в наличии: S, M, L, XL, 2XL\n"
            "Подбор размера (обхват груди):\n"
            "S — 88-92 см\n"
            "M — 92-96 см\n"
            "L — 96-100 см\n"
            "XL — 100-104 см\n"
            "2XL — 104-108 см\n\n"
            "Цвет: черный. Унисекс."
        ),
        "photos_dir": "2_hoodie_philipp_plein",
    },
    {
        "name": "Худи Yohji Yamamoto",
        "category": "Худи",
        "description": (
            "Плотный материал, отлично держит форму. "
            "Качественный принт с высокой стойкостью — не трескается при стирке. "
            "Удобный капюшон, свободная посадка. "
            "Унисекс — подходит как парням, так и девушкам.\n\n"
            "Размеры в наличии: S, M, L, XL, 2XL\n"
            "Подбор размера (обхват груди):\n"
            "S — 88-92 см\n"
            "M — 92-96 см\n"
            "L — 96-100 см\n"
            "XL — 100-104 см\n"
            "2XL — 104-108 см\n\n"
            "Цвет: черный. Товар новый."
        ),
        "photos_dir": "3_hoodie_yohji_yamamoto",
    },
    {
        "name": "Лонгслив Yohji Yamamoto",
        "category": "Лонгсливы",
        "description": (
            "Минималистичный дизайн с фирменным принтом. "
            "Мягкая, приятная к телу ткань. "
            "Качественный принт — не трескается, долго сохраняет внешний вид. "
            "Удобная посадка, идеально сочетается с джинсами, карго и шортами.\n\n"
            "Размеры в наличии: S, M, L, XL, 2XL\n"
            "Подбор размера (обхват груди):\n"
            "S — 88-92 см\n"
            "M — 92-96 см\n"
            "L — 96-100 см\n"
            "XL — 100-104 см\n"
            "2XL — 104-108 см\n\n"
            "Цвет: белый. Унисекс. Товар новый."
        ),
        "photos_dir": "4_longsleeve_yohji_yamamoto",
    },
    {
        "name": "Лонгслив Marcelo Burlon",
        "category": "Лонгсливы",
        "description": (
            "Приятная и мягкая ткань, комфортная посадка. "
            "Качественный и стойкий принт Marcelo Burlon Country of Milan. "
            "Подходит мужчинам и девушкам (унисекс). Идеально на каждый день.\n\n"
            "Размеры в наличии: S, M, L, XL, 2XL\n"
            "Подбор размера (обхват груди):\n"
            "S — 88-92 см\n"
            "M — 92-96 см\n"
            "L — 96-100 см\n"
            "XL — 100-104 см\n"
            "2XL — 104-108 см\n\n"
            "Цвет: черный. Товар новый."
        ),
        "photos_dir": "5_longsleeve_marcelo_burlon",
    },
    {
        "name": "Лонгслив Acne Studios Stockholm 1996",
        "category": "Лонгсливы",
        "description": (
            "Приятная к телу ткань, свободная и комфортная посадка. "
            "Стильный принт Acne Studios Stockholm 1996. "
            "Универсальный белый цвет — подходит под любой образ. "
            "Отлично сочетается с джинсами, карго, шортами и спортивными брюками.\n\n"
            "Размеры в наличии: S, M, L, XL, 2XL\n"
            "Подбор размера (обхват груди):\n"
            "S — 88-92 см\n"
            "M — 92-96 см\n"
            "L — 96-100 см\n"
            "XL — 100-104 см\n"
            "2XL — 104-108 см\n\n"
            "Цвет: белый. Унисекс. Товар новый. Стирать при 30-40 градусах на изнанку."
        ),
        "photos_dir": "6_longsleeve_acne_studios",
    },
    {
        "name": "AirPods Pro 2",
        "category": "Электроника",
        "description": (
            "Apple AirPods Pro 2 поколения.\n\n"
            "Активное шумоподавление (ANC) — эффективно блокирует внешние звуки.\n"
            "Режим прозрачности — слышите окружение, не снимая наушников.\n"
            "Пространственный звук с динамическим отслеживанием головы.\n"
            "Адаптивный эквалайзер, настраивается под форму вашего уха.\n"
            "До 6 часов работы на одном заряде, до 30 часов с зарядным кейсом.\n"
            "Зарядный кейс с поддержкой MagSafe и USB-C.\n"
            "Защита от воды и пота IPX4.\n\n"
            "В комплекте: наушники, зарядный кейс MagSafe, кабель USB-C, "
            "сменные амбушюры (XS / S / M / L).\n\n"
            "Совместимость: iPhone, iPad, Mac, Apple Watch. Товар новый."
        ),
        "photos_dir": "7_airpods_pro",
    },
]

CATEGORY_EMOJIS = {
    "Худи":        "🧥",
    "Лонгсливы":   "👕",
    "Электроника": "🎧",
}


async def main():
    print("=== Seed: загрузка товаров ===\n")
    await db.init_db()
    categories = await db.get_categories()
    products = await db.get_all_products(include_out_of_stock=True)
    category_ids = {category["name"]: category["id"] for category in categories}
    product_names = {product["name"] for product in products}

    for product in PRODUCTS:
        name = product["name"]
        if name in product_names:
            print(f"  Уже существует: {name}")
            continue
        category_id = category_ids.get(product["category"])
        if category_id is None:
            category_id = await db.add_category(
                product["category"],
                CATEGORY_EMOJIS.get(product["category"], "📦"),
            )
            category_ids[product["category"]] = category_id
        product_id = await db.add_product(
            category_id,
            name,
            product["description"],
            float(PRICES.get(name, 0)),
            photos=[],
            photo_folder="",
        )
        await db.update_product(product_id, "seed_folder", product["photos_dir"])
        print(f"  Добавлен товар id={product_id}: {name}")

    print("=== Готово! ===")
    if any(v == 0 for v in PRICES.values()):
        print(
            "\nВНИМАНИЕ: у некоторых товаров цена = 0.\n"
            "Установите цены через PRICES в этом файле и запустите повторно,\n"
            "или отредактируйте через админ-панель бота."
        )


if __name__ == "__main__":
    asyncio.run(main())
