from .start import router as start_router
from .catalog import router as catalog_router
from .search import router as search_router
from .reviews import router as reviews_router
from .admin.admin_main import router as admin_main_router
from .admin.admin_products import router as admin_products_router
from .admin.admin_categories import router as admin_categories_router
from .admin.admin_stats import router as admin_stats_router
from .admin.admin_settings import router as admin_settings_router

__all__ = [
    "start_router",
    "catalog_router",
    "search_router",
    "reviews_router",
    "admin_main_router",
    "admin_products_router",
    "admin_categories_router",
    "admin_stats_router",
    "admin_settings_router",
]
