from .audio import router as audio_router
from .auth import router as auth_router
from .catalog import router as catalog_router
from .profile import router as profile_router

__all__ = ["audio_router", "auth_router", "catalog_router", "profile_router"]
