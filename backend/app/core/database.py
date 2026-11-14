"""DB エンジンとセッションの管理。"""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """全テーブル共通の基底クラス。"""


def create_db_engine(database_url: str) -> Engine:
    is_sqlite = database_url.startswith("sqlite")
    # FastAPI はリクエストごとに別スレッドで動くため、SQLite のスレッドチェックを外す
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    engine = create_engine(database_url, connect_args=connect_args)

    if is_sqlite:
        # SQLite は既定で外部キー制約が無効なので、接続ごとに有効化する
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = create_db_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """リクエストごとに DB セッションを開き、終わったら閉じる（FastAPI の依存関数）。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
