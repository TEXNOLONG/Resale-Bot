import os
from dotenv import load_dotenv

load_dotenv()

# ─── Токены прямо в коде ───────────────────────────────────────────────────────
# Раскомментируй и заполни нужные строки — они перекроют переменные окружения.

# BOT_TOKEN_HARDCODED      = "123456:ABC-DEF..."
# DATABASE_URL_HARDCODED   = "postgresql://user:pass@host:5432/dbname"
# ADMIN_IDS_HARDCODED      = [123456789, 987654321]   # список Telegram ID
# SHOP_NAME_HARDCODED      = "Мой магазин"

# ─────────────────────────────────────────────────────────────────────────────

BOT_TOKEN    = locals().get("BOT_TOKEN_HARDCODED")    or os.getenv("BOT_TOKEN", "")
DATABASE_URL = locals().get("DATABASE_URL_HARDCODED") or os.getenv("DATABASE_URL", "")
SHOP_NAME    = locals().get("SHOP_NAME_HARDCODED")    or os.getenv("SHOP_NAME", "Магазин")

_ids_hc = locals().get("ADMIN_IDS_HARDCODED")
if _ids_hc:
    ADMIN_IDS: list[int] = list(_ids_hc)
else:
    ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN не задан!\n"
        "Вариант 1: установите переменную окружения BOT_TOKEN\n"
        "Вариант 2: раскомментируйте BOT_TOKEN_HARDCODED в config.py"
    )

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL не задан!\n"
        "Вариант 1: установите переменную окружения DATABASE_URL\n"
        "Вариант 2: раскомментируйте DATABASE_URL_HARDCODED в config.py"
    )
