"""
Скрипт для заполнения базы данных товарами из PDF.
Запускается один раз из папки bots/telegram-bot/

Требования:
  - BOT_TOKEN и DATABASE_URL в .env или переменных окружения
  - ADMIN_IDS — хотя бы один ID (в него будут отправлены фото для получения file_id)

Запуск:
  cd bots/telegram-bot
  python3.11 seed_products.py
"""

import asyncio
import os
import sys

from aiogram import Bot
from aiogram.types import FSInputFile
import asyncpg
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")

if not BOT_TOKEN:
    sys.exit("ERROR: BOT_TOKEN не задан")
if not DATABASE_URL:
    sys.exit("ERROR: DATABASE_URL не задан")

admin_ids = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip()]
if not admin_ids:
    sys.exit("ERROR: ADMIN_IDS не задан — нужен хотя бы один Telegram ID для загрузки фото")

UPLOADER_CHAT_ID = admin_ids[0]

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


async def upload_photos(bot: Bot, folder: str) -> list[str]:
    """Отправляет фото в чат админа и возвращает список file_id."""
    photo_dir = os.path.join(PHOTOS_DIR, folder)
    files = sorted(
        f for f in os.listdir(photo_dir) if f.lower().endswith((".jpeg", ".jpg", ".png"))
    )
    file_ids = []
    for fname in files:
        fpath = os.path.join(photo_dir, fname)
        msg = await bot.send_photo(
            chat_id=UPLOADER_CHAT_ID,
            photo=FSInputFile(fpath),
            caption=f"[seed] {folder}/{fname}",
        )
        file_id = msg.photo[-1].file_id
        file_ids.append(file_id)
        print(f"    Загружено: {fname} -> {file_id[:30]}...")
    return file_ids


async def get_or_create_category(pool: asyncpg.Pool, name: str) -> int:
    row = await pool.fetchrow("SELECT id FROM categories WHERE name=$1", name)
    if row:
        return row["id"]
    emoji = CATEGORY_EMOJIS.get(name, "")
    row = await pool.fetchrow(
        "INSERT INTO categories (name, emoji) VALUES ($1, $2) RETURNING id",
        name, emoji,
    )
    print(f"  Создана категория: {emoji} {name} (id={row['id']})")
    return row["id"]


async def product_exists(pool: asyncpg.Pool, name: str) -> bool:
    row = await pool.fetchrow("SELECT id FROM products WHERE name=$1", name)
    return row is not None


async def main():
    print("=== Seed: загрузка товаров ===\n")
    bot = Bot(token=BOT_TOKEN)
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)

    try:
        for product in PRODUCTS:
            name = product["name"]
            print(f"[{name}]")

            if await product_exists(pool, name):
                print(f"  Уже существует, пропускаем.\n")
                continue

            cat_id = await get_or_create_category(pool, product["category"])

            print(f"  Загрузка фото...")
            photos = await upload_photos(bot, product["photos_dir"])
            print(f"  Загружено фото: {len(photos)}")

            price = PRICES.get(name, 0)
            row = await pool.fetchrow(
                """INSERT INTO products (category_id, name, description, price, photos)
                   VALUES ($1, $2, $3, $4, $5) RETURNING id""",
                cat_id, name, product["description"], float(price), photos,
            )
            print(f"  Добавлен товар id={row['id']}, цена={price} руб.\n")

    finally:
        await pool.close()
        await bot.session.close()

    print("=== Готово! ===")
    if any(v == 0 for v in PRICES.values()):
        print(
            "\nВНИМАНИЕ: у некоторых товаров цена = 0.\n"
            "Установите цены через PRICES в этом файле и запустите повторно,\n"
            "или отредактируйте через админ-панель бота."
        )


if __name__ == "__main__":
    asyncio.run(main())
