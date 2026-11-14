"""古いスキーマの DB を起動時に移行できることの確認（アプリ本体とは別の一時 DB を使う）。"""

import pytest
from sqlalchemy import create_engine, inspect, text

from app.core.migrations import upgrade

# kind 列が無い時点の messages テーブル
OLD_MESSAGES_DDL = """
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT,
    image_path VARCHAR(100),
    created_at DATETIME NOT NULL,
    deleted_at DATETIME
)
"""


@pytest.fixture
def old_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text(OLD_MESSAGES_DDL))
        conn.execute(
            text(
                "INSERT INTO messages (id, room_id, user_id, content, image_path, created_at) "
                "VALUES (1, 1, 1, 'hi', NULL, '2026-01-01'), (2, 1, 1, NULL, 'a.png', '2026-01-01')"
            )
        )
    yield engine
    engine.dispose()


def test_upgrade_adds_kind_and_keeps_data(old_engine):
    upgrade(old_engine)

    with old_engine.connect() as conn:
        rows = conn.execute(text("SELECT id, kind, content FROM messages ORDER BY id")).all()
    assert rows == [(1, "text", "hi"), (2, "image", None)]
    # 他のテーブルも作成される
    assert inspect(old_engine).has_table("room_members")


def test_upgrade_is_idempotent(old_engine):
    upgrade(old_engine)
    upgrade(old_engine)


def test_upgrade_stops_on_unsupported_difference(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'older.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE messages (id INTEGER PRIMARY KEY, content TEXT)"))
    with pytest.raises(RuntimeError, match="Delete the database file"):
        upgrade(engine)
    engine.dispose()
