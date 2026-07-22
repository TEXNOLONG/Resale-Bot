import { Router, type IRouter } from "express";
import { pool } from "@workspace/db";
import {
  ListCategoriesResponse,
  ListProductsQueryParams,
  ListProductsResponse,
  GetProductParams,
  GetProductResponse,
  GetPhotoQueryParams,
  GetShopSettingsResponse,
  GetCatalogStatsResponse,
} from "@workspace/api-zod";

const router: IRouter = Router();

// ─── Categories ──────────────────────────────────────────────────────────────

router.get("/catalog/categories", async (_req, res): Promise<void> => {
  const result = await pool.query(`
    SELECT c.id, c.name, c.emoji, c.order_num,
           COUNT(p.id) FILTER (WHERE p.in_stock = true)::int AS product_count
    FROM categories c
    LEFT JOIN products p ON p.category_id = c.id
    GROUP BY c.id
    ORDER BY c.order_num, c.id
  `);
  res.json(ListCategoriesResponse.parse(result.rows));
});

// ─── Products ────────────────────────────────────────────────────────────────

router.get("/catalog/products", async (req, res): Promise<void> => {
  const params = ListProductsQueryParams.safeParse(req.query);
  if (!params.success) {
    res.status(400).json({ error: params.error.message });
    return;
  }

  const { category_id, q } = params.data;

  let sql = `
    SELECT p.id, p.name, p.description, p.price::float, p.category_id,
           c.name AS category_name, p.in_stock, p.views, p.photos
    FROM products p
    LEFT JOIN categories c ON c.id = p.category_id
    WHERE p.in_stock = true
  `;
  const values: unknown[] = [];

  if (category_id != null) {
    values.push(category_id);
    sql += ` AND p.category_id = $${values.length}`;
  }

  if (q) {
    values.push(`%${q.toLowerCase()}%`);
    sql += ` AND (LOWER(p.name) LIKE $${values.length} OR LOWER(p.description) LIKE $${values.length})`;
  }

  sql += " ORDER BY p.id DESC";

  const result = await pool.query(sql, values);
  const mapped = result.rows.map((r) => ({
    ...r,
    category_name: r.category_name ?? null,
  }));
  res.json(ListProductsResponse.parse(mapped));
});

// ─── Product detail ──────────────────────────────────────────────────────────

router.get("/catalog/products/:id", async (req, res): Promise<void> => {
  const raw = Array.isArray(req.params.id) ? req.params.id[0] : req.params.id;
  const params = GetProductParams.safeParse({ id: raw });
  if (!params.success) {
    res.status(400).json({ error: params.error.message });
    return;
  }

  // Track view
  await pool.query("UPDATE products SET views = views + 1 WHERE id = $1", [params.data.id]);

  const result = await pool.query(
    `SELECT p.id, p.name, p.description, p.price::float, p.category_id,
            c.name AS category_name, p.in_stock, p.views, p.photos
     FROM products p
     LEFT JOIN categories c ON c.id = p.category_id
     WHERE p.id = $1`,
    [params.data.id]
  );

  if (result.rows.length === 0) {
    res.status(404).json({ error: "Product not found" });
    return;
  }

  const row = result.rows[0];
  res.json(GetProductResponse.parse({ ...row, category_name: row.category_name ?? null }));
});

// ─── Photo proxy ─────────────────────────────────────────────────────────────

const filePathCache = new Map<string, string>();

router.get("/catalog/photo", async (req, res): Promise<void> => {
  const params = GetPhotoQueryParams.safeParse(req.query);
  if (!params.success) {
    res.status(400).json({ error: "Missing file_id" });
    return;
  }

  const { file_id } = params.data;
  const BOT_TOKEN = process.env.BOT_TOKEN;

  if (!BOT_TOKEN) {
    res.status(500).json({ error: "BOT_TOKEN not configured" });
    return;
  }

  try {
    let filePath = filePathCache.get(file_id);

    if (!filePath) {
      const tgRes = await fetch(
        `https://api.telegram.org/bot${BOT_TOKEN}/getFile?file_id=${encodeURIComponent(file_id)}`
      );
      const tgData = (await tgRes.json()) as { ok: boolean; result?: { file_path: string } };

      if (!tgData.ok || !tgData.result?.file_path) {
        res.status(404).json({ error: "File not found" });
        return;
      }

      filePath = tgData.result.file_path;
      filePathCache.set(file_id, filePath);
    }

    res.redirect(`https://api.telegram.org/file/bot${BOT_TOKEN}/${filePath}`);
  } catch {
    res.status(502).json({ error: "Failed to fetch from Telegram" });
  }
});

// ─── Shop settings ───────────────────────────────────────────────────────────

router.get("/catalog/settings", async (_req, res): Promise<void> => {
  const result = await pool.query("SELECT key, value FROM settings");
  const map: Record<string, string> = {};
  for (const row of result.rows) map[row.key] = row.value;

  res.json(
    GetShopSettingsResponse.parse({
      shop_name: process.env.SHOP_NAME ?? "veachelsell",
      welcome_text: map["welcome_text"] ?? "Привет! Выберите нужный раздел:",
      contact_info: map["contact_info"] ?? "",
      welcome_photo: map["welcome_photo"] ?? null,
    })
  );
});

// ─── Stats ───────────────────────────────────────────────────────────────────

router.get("/catalog/stats", async (_req, res): Promise<void> => {
  const [counts, topRow] = await Promise.all([
    pool.query(
      `SELECT
        (SELECT COUNT(*)::int FROM products WHERE in_stock = true) AS total_products,
        (SELECT COUNT(*)::int FROM categories) AS total_categories`
    ),
    pool.query(
      `SELECT p.id, p.name, p.description, p.price::float, p.category_id,
              c.name AS category_name, p.in_stock, p.views, p.photos
       FROM products p
       LEFT JOIN categories c ON c.id = p.category_id
       WHERE p.in_stock = true
       ORDER BY p.views DESC
       LIMIT 1`
    ),
  ]);

  const { total_products, total_categories } = counts.rows[0];
  const topProduct =
    topRow.rows.length > 0
      ? { ...topRow.rows[0], category_name: topRow.rows[0].category_name ?? null }
      : undefined;

  res.json(
    GetCatalogStatsResponse.parse({
      total_products,
      total_categories,
      ...(topProduct ? { top_product: topProduct } : {}),
    })
  );
});

export default router;
