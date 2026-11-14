"""起動時の DB スキーマ準備。

create_all は「無いテーブルを作る」だけで、既存テーブルへの列追加は行わない。
そのため、既存データを保ったまま追加できる列はここで ALTER TABLE し、
それ以外の不一致は分かりやすいエラーで停止する。

本格運用ではマイグレーションツール（Alembic）に置き換える想定。
"""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db import Base


def _messages_columns(engine: Engine) -> set[str] | None:
    inspector = inspect(engine)
    if not inspector.has_table("messages"):
        return None
    return {c["name"] for c in inspector.get_columns("messages")}


def _add_message_kind(engine: Engine) -> None:
    """messages.kind（メッセージの種類）を追加し、既存の行を埋める。"""
    with engine.begin() as conn:
        conn.execute(
            text("ALTER TABLE messages ADD COLUMN kind VARCHAR(20) NOT NULL DEFAULT 'text'")
        )
        conn.execute(text("UPDATE messages SET kind = 'image' WHERE image_path IS NOT NULL"))


# 既存データを保ったまま自動で追加できる列: 列名 -> 追加処理
_AUTO_MIGRATIONS = {"kind": _add_message_kind}


def upgrade(engine: Engine) -> None:
    columns = _messages_columns(engine)
    if columns is not None:
        missing = {c.name for c in Base.metadata.tables["messages"].columns} - columns
        # 自動で追加できない列が欠けていれば、DB には一切手を付けずに停止する
        unsupported = missing - _AUTO_MIGRATIONS.keys()
        if unsupported:
            raise RuntimeError(
                "Database schema is outdated "
                f"(messages is missing: {', '.join(sorted(unsupported))}). "
                "Delete the database file (e.g. backend/chat.db) and restart."
            )
        for column in sorted(missing):
            _AUTO_MIGRATIONS[column](engine)
    Base.metadata.create_all(bind=engine)
