"""FastAPI アプリケーションのエントリポイント。

起動: uv run uvicorn app.main:app --reload
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, members, messages, rooms, websocket
from app.core import migrations
from app.core.config import get_settings
from app.core.database import engine
from app.core.errors import AppError
from app.storage import images


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    migrations.upgrade(engine)  # テーブル作成と、必要な列の自動追加
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Simple Chat API", version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # サービス層のドメイン例外を、対応する HTTP ステータスのレスポンスに変換する
    @app.exception_handler(AppError)
    async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/docs")

    @app.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for module in (auth, rooms, members, messages, websocket):
        app.include_router(module.router)

    # アップロード画像の配信（ファイル名は推測できない UUID）
    app.mount("/uploads", StaticFiles(directory=images.upload_dir()), name="uploads")
    return app


app = create_app()
