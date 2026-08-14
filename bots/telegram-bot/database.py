"""
Локальное JSON-хранилище магазина.

Файл данных: bots/telegram-bot/data/store.json
JSON выбран для запуска на небольшом VPS без отдельного PostgreSQL-сервера.
Все публичные функции оставляют прежний async-интерфейс, поэтому обработчики
бота не зависят от способа хранения данных.
"""

import asyncio
import json
import os
import tempfile
from datetime import date, datetime, timezone
from typing import Any


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "store.json")

_store: dict[str, Any] | None = None
_lock = asyncio.Lock()

_COLLECTIONS = (
    "users",
    "categories",
    "products",
    "reviews",
    "product_clicks",
    "favorites",
    "orders",
)
_COUNTER_NAMES = (
    "users",
    "categories",
    "products",
    "reviews",
    "product_clicks",
    "orders",
)
_DATE_FIELDS = ("created_at",)


def _empty_store() -> dict[str, Any]:
    return {
        "settings": {},
        **{name: [] for name in _COLLECTIONS},
        "counters": {name: 0 for name in _COUNTER_NAMES},
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def _public(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    for field in _DATE_FIELDS:
        if field in result:
            result[field] = _as_datetime(result[field])
    return result


def _public_many(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_public(row) for row in rows]


def _state() -> dict[str, Any]:
    if _store is None:
        raise RuntimeError("JSON-хранилище ещё не инициализировано")
    return _store


def _next_id_locked(collection: str) -> int:
    store = _state()
    store["counters"][collection] = int(store["counters"].get(collection, 0)) + 1
    return store["counters"][collection]


def _save_locked() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix="store-", suffix=".json", dir=DATA_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(_state(), file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, DATA_FILE)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def _category_name_locked(category_id: int | None) -> str | None:
    if category_id is None:
        return None
    for category in _state()["categories"]:
        if category["id"] == category_id:
            return category["name"]
    return None


def _product_view_locked(product: dict[str, Any]) -> dict[str, Any]:
    result = dict(product)
    result["cat_name"] = _category_name_locked(result.get("category_id"))
    return result


async def init_db():
    """Создаёт или загружает JSON-файл данных и автоматически добавляет seed-каталог."""
    global _store
    async with _lock:
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, encoding="utf-8") as file:
                    loaded = json.load(file)
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Не удалось прочитать {DATA_FILE}: {exc}") from exc
            if not isinstance(loaded, dict):
                raise RuntimeError(f"Файл {DATA_FILE} должен содержать JSON-объект")
            _store = _empty_store()
            for key, value in loaded.items():
                if key in _store:
                    _store[key] = value
            for collection in _COLLECTIONS:
                if not isinstance(_store.get(collection), list):
                    _store[collection] = []
            if not isinstance(_store.get("settings"), dict):
                _store["settings"] = {}
            if not isinstance(_store.get("counters"), dict):
                _store["counters"] = {}
        else:
            _store = _empty_store()

        # Восстанавливаем счётчики даже после ручного редактирования JSON.
        for collection in _COUNTER_NAMES:
            largest_id = max(
                (int(row.get("id", 0)) for row in _state()[collection]),
                default=0,
            )
            _state()["counters"][collection] = max(
                int(_state()["counters"].get(collection, 0)), largest_id
            )

        # При первом запуске сохраняем каталог из seed_products.py. Фото остаются
        # на диске в seed_photos и не отправляются пользователям все сразу.
        if not _state()["products"] and os.path.isdir(os.path.join(BASE_DIR, "seed_photos")):
            from seed_products import CATEGORY_EMOJIS, PRICES, PRODUCTS

            categories_by_name: dict[str, int] = {}
            for product in PRODUCTS:
                category_name = product["category"]
                category_id = categories_by_name.get(category_name)
                if category_id is None:
                    category_id = _next_id_locked("categories")
                    _state()["categories"].append(
                        {
                            "id": category_id,
                            "name": category_name,
                            "emoji": CATEGORY_EMOJIS.get(category_name, "📦"),
                            "order_num": category_id,
                        }
                    )
                    categories_by_name[category_name] = category_id
                product_id = _next_id_locked("products")
                _state()["products"].append(
                    {
                        "id": product_id,
                        "name": product["name"],
                        "description": product.get("description", ""),
                        "price": float(PRICES.get(product["name"], 0)),
                        "category_id": category_id,
                        "in_stock": True,
                        "views": 0,
                        "photos": [],
                        "photo_folder": "",
                        "seed_folder": product["photos_dir"],
                    }
                )

        _save_locked()


async def close_pool():
    """Совместимость с прежним main.py: JSON уже сохраняется после каждой записи."""
    async with _lock:
        if _store is not None:
            _save_locked()


# ─── Settings ────────────────────────────────────────────────────────────────

async def get_setting(key: str) -> str:
    async with _lock:
        return str(_state()["settings"].get(key, ""))


async def set_setting(key: str, value: str):
    async with _lock:
        _state()["settings"][key] = value
        _save_locked()


# ─── Users ───────────────────────────────────────────────────────────────────

async def upsert_user(telegram_id: int, username: str, first_name: str, last_name: str):
    async with _lock:
        store = _state()
        user = next(
            (item for item in store["users"] if item["telegram_id"] == telegram_id),
            None,
        )
        if user is None:
            user = {
                "id": _next_id_locked("users"),
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "created_at": _now(),
            }
            store["users"].append(user)
        else:
            user.update(
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
        _save_locked()


async def get_users_count() -> int:
    async with _lock:
        return len(_state()["users"])


async def get_new_users_today() -> int:
    today = date.today()
    async with _lock:
        return sum(
            1
            for user in _state()["users"]
            if _as_datetime(user.get("created_at")).date() == today
        )


# ─── Categories ──────────────────────────────────────────────────────────────

async def get_categories() -> list:
    async with _lock:
        rows = sorted(
            _state()["categories"],
            key=lambda item: (item.get("order_num", 0), item["id"]),
        )
        return _public_many(rows)


async def get_category(category_id: int):
    async with _lock:
        row = next(
            (item for item in _state()["categories"] if item["id"] == category_id),
            None,
        )
        return _public(row)


async def add_category(name: str, emoji: str) -> int:
    async with _lock:
        category_id = _next_id_locked("categories")
        _state()["categories"].append(
            {
                "id": category_id,
                "name": name,
                "emoji": emoji,
                "order_num": category_id,
            }
        )
        _save_locked()
        return category_id


async def delete_category(category_id: int):
    async with _lock:
        _state()["categories"] = [
            item for item in _state()["categories"] if item["id"] != category_id
        ]
        for product in _state()["products"]:
            if product.get("category_id") == category_id:
                product["category_id"] = None
        _save_locked()


# ─── Products ────────────────────────────────────────────────────────────────

async def get_products_by_category(category_id: int) -> list:
    async with _lock:
        rows = [
            _product_view_locked(item)
            for item in _state()["products"]
            if item.get("category_id") == category_id and item.get("in_stock", True)
        ]
        rows.sort(key=lambda item: item["id"], reverse=True)
        return _public_many(rows)


async def get_all_products(include_out_of_stock: bool = False) -> list:
    async with _lock:
        rows = [
            _product_view_locked(item)
            for item in _state()["products"]
            if include_out_of_stock or item.get("in_stock", True)
        ]
        rows.sort(key=lambda item: item["id"], reverse=True)
        return _public_many(rows)


async def get_product(product_id: int):
    async with _lock:
        row = next(
            (item for item in _state()["products"] if item["id"] == product_id),
            None,
        )
        return _public(_product_view_locked(row)) if row else None


async def search_products(query: str) -> list:
    needle = query.casefold()
    async with _lock:
        rows = [
            _product_view_locked(item)
            for item in _state()["products"]
            if item.get("in_stock", True)
            and (
                needle in str(item.get("name", "")).casefold()
                or needle in str(item.get("description", "")).casefold()
            )
        ]
        rows.sort(key=lambda item: item["id"], reverse=True)
        return _public_many(rows)


async def add_product(
    category_id: int,
    name: str,
    description: str,
    price: float,
    photos: list,
    photo_folder: str = "",
) -> int:
    async with _lock:
        product_id = _next_id_locked("products")
        _state()["products"].append(
            {
                "id": product_id,
                "name": name,
                "description": description,
                "price": float(price),
                "category_id": category_id,
                "in_stock": True,
                "views": 0,
                "photos": list(photos or []),
                "photo_folder": photo_folder,
                "seed_folder": "",
            }
        )
        _save_locked()
        return product_id


async def update_product(product_id: int, field: str, value):
    allowed = {"name", "description", "price", "in_stock", "photo_folder", "seed_folder"}
    if field not in allowed:
        raise ValueError(f"Field {field} not allowed")
    async with _lock:
        product = next(
            (item for item in _state()["products"] if item["id"] == product_id),
            None,
        )
        if product is None:
            raise ValueError(f"Product {product_id} not found")
        if field == "price":
            value = float(value)
        product[field] = value
        _save_locked()


async def delete_product(product_id: int):
    async with _lock:
        _state()["products"] = [
            item for item in _state()["products"] if item["id"] != product_id
        ]
        _state()["favorites"] = [
            item for item in _state()["favorites"] if item["product_id"] != product_id
        ]
        _state()["product_clicks"] = [
            item for item in _state()["product_clicks"] if item["product_id"] != product_id
        ]
        for order in _state()["orders"]:
            if order.get("product_id") == product_id:
                order["product_id"] = None
        _save_locked()


async def increment_views(product_id: int):
    async with _lock:
        product = next(
            (item for item in _state()["products"] if item["id"] == product_id),
            None,
        )
        if product:
            product["views"] = int(product.get("views", 0)) + 1
            _save_locked()


async def add_product_click(product_id: int, user_id: int):
    async with _lock:
        _state()["product_clicks"].append(
            {
                "id": _next_id_locked("product_clicks"),
                "product_id": product_id,
                "user_id": user_id,
                "created_at": _now(),
            }
        )
        _save_locked()


# ─── Reviews ─────────────────────────────────────────────────────────────────

async def get_approved_reviews(limit: int = 10, offset: int = 0) -> list:
    async with _lock:
        rows = [
            item for item in _state()["reviews"] if item.get("is_approved", False)
        ]
        rows.sort(key=lambda item: _as_datetime(item.get("created_at")), reverse=True)
        return _public_many(rows[offset : offset + limit])


async def get_pending_reviews() -> list:
    async with _lock:
        rows = [
            item for item in _state()["reviews"] if not item.get("is_approved", False)
        ]
        rows.sort(key=lambda item: _as_datetime(item.get("created_at")), reverse=True)
        return _public_many(rows)


async def add_review(
    user_id: int,
    username: str,
    text: str,
    rating: int,
    photo_file_id: str = None,
) -> int:
    async with _lock:
        review_id = _next_id_locked("reviews")
        _state()["reviews"].append(
            {
                "id": review_id,
                "user_id": user_id,
                "username": username,
                "text": text,
                "rating": int(rating),
                "photo_file_id": photo_file_id,
                "is_approved": False,
                "created_at": _now(),
            }
        )
        _save_locked()
        return review_id


async def approve_review(review_id: int):
    async with _lock:
        for review in _state()["reviews"]:
            if review["id"] == review_id:
                review["is_approved"] = True
                break
        _save_locked()


async def delete_review(review_id: int):
    async with _lock:
        _state()["reviews"] = [
            item for item in _state()["reviews"] if item["id"] != review_id
        ]
        _save_locked()


async def get_reviews_count() -> int:
    async with _lock:
        return sum(1 for item in _state()["reviews"] if item.get("is_approved", False))


# ─── Stats ───────────────────────────────────────────────────────────────────

async def get_top_products(limit: int = 10) -> list:
    async with _lock:
        rows = [
            {
                "id": item["id"],
                "name": item["name"],
                "price": item["price"],
                "views": int(item.get("views", 0)),
                "in_stock": item.get("in_stock", True),
            }
            for item in _state()["products"]
        ]
        rows.sort(key=lambda item: item["views"], reverse=True)
        return _public_many(rows[:limit])


async def get_top_clicked_products(limit: int = 10) -> list:
    async with _lock:
        click_counts: dict[int, int] = {}
        for click in _state()["product_clicks"]:
            product_id = click["product_id"]
            click_counts[product_id] = click_counts.get(product_id, 0) + 1
        rows = []
        for product in _state()["products"]:
            rows.append(
                {
                    "id": product["id"],
                    "name": product["name"],
                    "price": product["price"],
                    "clicks": click_counts.get(product["id"], 0),
                }
            )
        rows.sort(key=lambda item: item["clicks"], reverse=True)
        return _public_many(rows[:limit])


async def get_total_clicks() -> int:
    async with _lock:
        return len(_state()["product_clicks"])


# ─── Favorites ───────────────────────────────────────────────────────────────

async def add_favorite(user_id: int, product_id: int):
    async with _lock:
        exists = any(
            item["user_id"] == user_id and item["product_id"] == product_id
            for item in _state()["favorites"]
        )
        if not exists:
            _state()["favorites"].append(
                {"user_id": user_id, "product_id": product_id}
            )
            _save_locked()


async def remove_favorite(user_id: int, product_id: int):
    async with _lock:
        _state()["favorites"] = [
            item
            for item in _state()["favorites"]
            if not (item["user_id"] == user_id and item["product_id"] == product_id)
        ]
        _save_locked()


async def is_favorite(user_id: int, product_id: int) -> bool:
    async with _lock:
        return any(
            item["user_id"] == user_id and item["product_id"] == product_id
            for item in _state()["favorites"]
        )


async def get_user_favorites(user_id: int) -> list:
    async with _lock:
        product_ids = {
            item["product_id"]
            for item in _state()["favorites"]
            if item["user_id"] == user_id
        }
        rows = [
            _product_view_locked(item)
            for item in _state()["products"]
            if item["id"] in product_ids
        ]
        rows.sort(key=lambda item: item["id"], reverse=True)
        return _public_many(rows)


# ─── Orders ──────────────────────────────────────────────────────────────────

async def create_order(
    user_id: int,
    username: str,
    first_name: str,
    product_id: int,
    product_name: str,
    product_price: float,
    comment: str = "",
) -> int:
    async with _lock:
        order_id = _next_id_locked("orders")
        _state()["orders"].append(
            {
                "id": order_id,
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "product_id": product_id,
                "product_name": product_name,
                "product_price": float(product_price),
                "comment": comment,
                "status": "new",
                "created_at": _now(),
            }
        )
        _save_locked()
        return order_id


async def get_orders(limit: int = 50) -> list:
    async with _lock:
        rows = sorted(
            _state()["orders"],
            key=lambda item: _as_datetime(item.get("created_at")),
            reverse=True,
        )
        return _public_many(rows[:limit])


async def get_order(order_id: int):
    async with _lock:
        row = next(
            (item for item in _state()["orders"] if item["id"] == order_id),
            None,
        )
        return _public(row)


async def get_orders_count() -> int:
    async with _lock:
        return len(_state()["orders"])