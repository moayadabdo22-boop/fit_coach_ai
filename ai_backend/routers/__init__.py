from .users import router as users_router
from .plans import router as plans_router
from .analytics import router as analytics_router
from .ai import router as ai_router
from .admin import router as admin_router

__all__ = ["users_router", "plans_router", "analytics_router", "ai_router", "admin_router"]

