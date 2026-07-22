import asyncpg
from config import DATABASE_URL

_pool: asyncpg.Pool = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def init_db():
    pool = await get_pool()
    await pool.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            emoji TEXT NOT NULL DEFAULT '',
            order_num INT NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            price NUMERIC(12,2) NOT NULL DEFAULT 0,
            category_id INT REFERENCES categories(id) ON DELETE SET NULL,
            in_stock BOOLEAN NOT NULL DEFAULT TRUE,
            views INT NOT NULL DEFAULT 0,
            photos TEXT[] NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            username TEXT,
            text TEXT NOT NULL DEFAULT '',
            rating INT NOT NULL DEFAULT 5,
            photo_file_id TEXT,
            is_approved BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS product_clicks (
            id SERIAL PRIMARY KEY,
            product_id INT REFERENCES products(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)


# ─── Settings ──────────────────────────────────────────────────────────────

async def get_setting(key: str) -> str:
    pool = await get_pool()
    row = await pool.fetchrow("SELECT value FROM settings WHERE key=$1", key)
    return row["value"] if row else ""


async def set_setting(key: str, value: str):
    pool = await get_pool()
    await pool.execute(
        "INSERT INTO settings (key, value) VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET value=$2",
        key, value
    )


# ─── Users ─────────────────────────────────────────────────────────────────

async def upsert_user(telegram_id: int, username: str, first_name: str, last_name: str):
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO users (telegram_id, username, first_name, last_name)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (telegram_id) DO UPDATE
           SET username=$2, first_name=$3, last_name=$4""",
        telegram_id, username, first_name, last_name
    )


async def get_users_count() -> int:
    pool = await get_pool()
    row = await pool.fetchrow("SELECT COUNT(*) as cnt FROM users")
    return row["cnt"]


async def get_new_users_today() -> int:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT COUNT(*) as cnt FROM users WHERE created_at >= CURRENT_DATE"
    )
    return row["cnt"]


# ─── Categories ────────────────────────────────────────────────────────────

async def get_categories() -> list:
    pool = await get_pool()
    return await pool.fetch("SELECT * FROM categories ORDER BY order_num, id")


async def get_category(category_id: int):
    pool = await get_pool()
    return await pool.fetchrow("SELECT * FROM categories WHERE id=$1", category_id)


async def add_category(name: str, emoji: str) -> int:
    pool = await get_pool()
    row = await pool.fetchrow(
        "INSERT INTO categories (name, emoji) VALUES ($1, $2) RETURNING id",
        name, emoji
    )
    return row["id"]


async def delete_category(category_id: int):
    pool = await get_pool()
    await pool.execute("DELETE FROM categories WHERE id=$1", category_id)


# ─── Products ──────────────────────────────────────────────────────────────

async def get_products_by_category(category_id: int) -> list:
    pool = await get_pool()
    return await pool.fetch(
        "SELECT * FROM products WHERE category_id=$1 AND in_stock=TRUE ORDER BY id DESC",
        category_id
    )


async def get_all_products(include_out_of_stock: bool = False) -> list:
    pool = await get_pool()
    if include_out_of_stock:
        return await pool.fetch(
            "SELECT p.*, c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id ORDER BY p.id DESC"
        )
    return await pool.fetch(
        "SELECT p.*, c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.in_stock=TRUE ORDER BY p.id DESC"
    )


async def get_product(product_id: int):
    pool = await get_pool()
    return await pool.fetchrow(
        "SELECT p.*, c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.id=$1",
        product_id
    )


async def search_products(query: str) -> list:
    pool = await get_pool()
    return await pool.fetch(
        "SELECT p.*, c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE (LOWER(p.name) LIKE $1 OR LOWER(p.description) LIKE $1) AND p.in_stock=TRUE ORDER BY p.id DESC",
        f"%{query.lower()}%"
    )


async def add_product(category_id: int, name: str, description: str, price: float, photos: list) -> int:
    pool = await get_pool()
    row = await pool.fetchrow(
        "INSERT INTO products (category_id, name, description, price, photos) VALUES ($1, $2, $3, $4, $5) RETURNING id",
        category_id, name, description, price, photos
    )
    return row["id"]


async def update_product(product_id: int, field: str, value):
    pool = await get_pool()
    allowed = {"name", "description", "price", "in_stock"}
    if field not in allowed:
        raise ValueError(f"Field {field} not allowed")
    await pool.execute(f"UPDATE products SET {field}=$1 WHERE id=$2", value, product_id)


async def delete_product(product_id: int):
    pool = await get_pool()
    await pool.execute("DELETE FROM products WHERE id=$1", product_id)


async def increment_views(product_id: int):
    pool = await get_pool()
    await pool.execute("UPDATE products SET views=views+1 WHERE id=$1", product_id)


async def add_product_click(product_id: int, user_id: int):
    pool = await get_pool()
    await pool.execute(
        "INSERT INTO product_clicks (product_id, user_id) VALUES ($1, $2)",
        product_id, user_id
    )


# ─── Reviews ───────────────────────────────────────────────────────────────

async def get_approved_reviews(limit: int = 10, offset: int = 0) -> list:
    pool = await get_pool()
    return await pool.fetch(
        "SELECT * FROM reviews WHERE is_approved=TRUE ORDER BY created_at DESC LIMIT $1 OFFSET $2",
        limit, offset
    )


async def get_pending_reviews() -> list:
    pool = await get_pool()
    return await pool.fetch("SELECT * FROM reviews WHERE is_approved=FALSE ORDER BY created_at DESC")


async def add_review(user_id: int, username: str, text: str, rating: int, photo_file_id: str = None) -> int:
    pool = await get_pool()
    row = await pool.fetchrow(
        "INSERT INTO reviews (user_id, username, text, rating, photo_file_id) VALUES ($1, $2, $3, $4, $5) RETURNING id",
        user_id, username, text, rating, photo_file_id
    )
    return row["id"]


async def approve_review(review_id: int):
    pool = await get_pool()
    await pool.execute("UPDATE reviews SET is_approved=TRUE WHERE id=$1", review_id)


async def delete_review(review_id: int):
    pool = await get_pool()
    await pool.execute("DELETE FROM reviews WHERE id=$1", review_id)


async def get_reviews_count() -> int:
    pool = await get_pool()
    row = await pool.fetchrow("SELECT COUNT(*) as cnt FROM reviews WHERE is_approved=TRUE")
    return row["cnt"]


# ─── Stats ─────────────────────────────────────────────────────────────────

async def get_top_products(limit: int = 10) -> list:
    pool = await get_pool()
    return await pool.fetch(
        "SELECT id, name, price, views, in_stock FROM products ORDER BY views DESC LIMIT $1",
        limit
    )


async def get_top_clicked_products(limit: int = 10) -> list:
    pool = await get_pool()
    return await pool.fetch(
        """SELECT p.id, p.name, p.price, COUNT(pc.id) as clicks
           FROM products p
           LEFT JOIN product_clicks pc ON p.id=pc.product_id
           GROUP BY p.id, p.name, p.price
           ORDER BY clicks DESC
           LIMIT $1""",
        limit
    )


async def get_total_clicks() -> int:
    pool = await get_pool()
    row = await pool.fetchrow("SELECT COUNT(*) as cnt FROM product_clicks")
    return row["cnt"]
