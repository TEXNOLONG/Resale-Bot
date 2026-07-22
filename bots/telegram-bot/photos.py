"""
Утилиты для работы с фотографиями товаров.

Конвенция имён файлов: 1.jpg, 2.png, 3.jpeg … (до 10 штук на товар).
Также поддерживает старый формат photo_01.jpeg (любое число в имени файла).
"""

import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCT_PHOTOS_DIR = os.path.join(BASE_DIR, "product_photos")
SEED_PHOTOS_DIR    = os.path.join(BASE_DIR, "seed_photos")

_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _extract_num(filename: str) -> int:
    """Извлекает первое число из имени файла (без расширения)."""
    name = os.path.splitext(filename)[0]
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else 9999


def get_local_photos(folder: str) -> list[str]:
    """
    Возвращает список путей к фото из папки, отсортированных по номеру.
    Поддерживает: 1.jpg, 2.png, photo_01.jpeg и т.п.
    """
    if not folder or not os.path.isdir(folder):
        return []
    files = []
    for f in os.listdir(folder):
        if os.path.splitext(f)[1].lower() in _EXTENSIONS:
            files.append((_extract_num(f), os.path.join(folder, f)))
    files.sort(key=lambda x: x[0])
    return [path for _, path in files]


def get_product_photo_folder(product_id: int) -> str:
    """Папка для автоматически загруженных фото товара (через бота)."""
    return os.path.join(PRODUCT_PHOTOS_DIR, f"prod_{product_id}")


def ensure_product_photo_folder(product_id: int) -> str:
    """Создаёт и возвращает папку для фото товара."""
    folder = get_product_photo_folder(product_id)
    os.makedirs(folder, exist_ok=True)
    return folder


def next_photo_number(folder: str) -> int:
    """Следующий свободный номер для нового фото в папке."""
    photos = get_local_photos(folder)
    if not photos:
        return 1
    nums = [_extract_num(os.path.basename(p)) for p in photos]
    return max(nums) + 1


def get_all_product_photos(product: dict) -> list[tuple[str, str]]:
    """
    Возвращает список (type, source) для всех фото товара.
    type = 'file'   → source = абсолютный путь к файлу (используй FSInputFile)
    type = 'fileid' → source = Telegram file_id
    """
    product_id = product.get("id")

    # 1. Явно указанная папка (photo_folder в БД)
    folder = product.get("photo_folder", "") or ""
    if folder and os.path.isdir(folder):
        local = get_local_photos(folder)
        if local:
            return [("file", p) for p in local]

    # 2. Автоматическая папка product_photos/prod_<id>/
    if product_id:
        auto_folder = get_product_photo_folder(product_id)
        local = get_local_photos(auto_folder)
        if local:
            return [("file", p) for p in local]

    # 3. Seed-фото (seed_photos/<subfolder>/ — для совместимости)
    seed_sub = product.get("seed_folder", "") or ""
    if seed_sub:
        seed_folder = os.path.join(SEED_PHOTOS_DIR, seed_sub)
        local = get_local_photos(seed_folder)
        if local:
            return [("file", p) for p in local]

    # 4. Telegram file_ids из БД
    file_ids = product.get("photos") or []
    return [("fileid", fid) for fid in file_ids if fid]
