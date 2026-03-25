from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .middleware import add_security_headers
from .routers.audio import router as audio_router
from .routers.auth import router as auth_router
from .routers.catalog import router as catalog_router
from .routers.profile import router as profile_router
from .runtime import db_config, ensure_runtime_directories, settings


def create_app() -> FastAPI:
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(add_security_headers)

    @app.on_event("startup")
    async def startup_event():
        ensure_runtime_directories()
        await db_config.init_models()

    app.include_router(auth_router)
    app.include_router(audio_router)
    app.include_router(profile_router)
    app.include_router(catalog_router)
    return app


app = create_app()
