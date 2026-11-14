"""FastAPI アプリケーションのエントリポイント。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.errors import AppError
from app.routers import auth, messages, rooms, ws
from app.services.rooms import ensure_room


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_room(db, get_settings().default_room_name)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Simple Chat API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in (auth.router, rooms.router, messages.router, ws.router):
        app.include_router(router)
    return app


app = create_app()
