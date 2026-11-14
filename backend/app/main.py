"""FastAPI アプリケーションのエントリポイント。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect

from app import storage
from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.errors import AppError
from app.routers import auth, messages, rooms, ws
from app.services.rooms import ensure_room


def init_db() -> None:
    _check_schema_is_current()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_room(db, get_settings().default_room_name)


def _check_schema_is_current() -> None:
    """create_all は既存テーブルに列を追加しないため、古い DB なら分かりやすく停止する。

    本格運用ではマイグレーションツール（Alembic）で対応する。
    """
    inspector = inspect(engine)
    if not inspector.has_table("messages"):
        return
    existing = {c["name"] for c in inspector.get_columns("messages")}
    missing = {c.name for c in Base.metadata.tables["messages"].columns} - existing
    if missing:
        raise RuntimeError(
            f"Database schema is outdated (messages is missing: {', '.join(sorted(missing))}). "
            "Delete the database file (e.g. backend/chat.db) and restart."
        )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Simple Chat API", version="0.2.0", lifespan=lifespan)

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

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/docs")

    @app.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in (auth.router, rooms.router, messages.router, ws.router):
        app.include_router(router)

    # アップロード画像の配信（ファイル名は推測不能な UUID）
    app.mount("/uploads", StaticFiles(directory=storage.upload_dir()), name="uploads")
    return app


app = create_app()
