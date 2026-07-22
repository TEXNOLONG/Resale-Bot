import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
SHOP_NAME = os.getenv("SHOP_NAME", "Магазин")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан! Установите переменную окружения BOT_TOKEN.")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL не задан!")
