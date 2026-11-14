"""テスト共通のフィクスチャとヘルパー。

各テストは空の DB から始まる。よく使う登場人物：
- alice, bob : ログイン済みユーザー（値は Authorization ヘッダー）
- room_id    : alice が作成し、bob も参加しているルーム「lobby」
"""

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

# app を import する前に、テスト用の DB と保存先を指定する
_tmpdir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmpdir) / 'test.db'}"
os.environ["UPLOAD_DIR"] = str(Path(_tmpdir) / "uploads")
os.environ["MAX_IMAGE_BYTES"] = "1024"  # 上限超過を試しやすくする

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

Headers = dict[str, str]


# ---- フィクスチャ ----
@pytest.fixture
def client() -> Iterator[TestClient]:
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:  # 起動処理（lifespan）でテーブルが作られる
        yield c


@pytest.fixture
def alice(client: TestClient) -> Headers:
    return login(client, "alice")


@pytest.fixture
def bob(client: TestClient) -> Headers:
    return login(client, "bob")


@pytest.fixture
def room_id(client: TestClient, alice: Headers, bob: Headers) -> int:
    """alice が作成し、bob も参加しているルーム「lobby」。"""
    room_id = create_room(client, alice, "lobby")
    assert client.put(f"/api/rooms/{room_id}/members/me", headers=bob).status_code == 200
    return room_id


# ---- API 呼び出しのヘルパー ----
def login(client: TestClient, name: str) -> Headers:
    res = client.post("/api/auth/login", json={"name": name})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['token']}"}


def create_room(client: TestClient, headers: Headers, name: str) -> int:
    res = client.post("/api/rooms", json={"name": name}, headers=headers)
    assert res.status_code == 201
    return res.json()["id"]


def get_room(client: TestClient, headers: Headers, room_id: int) -> dict:
    return client.get(f"/api/rooms/{room_id}", headers=headers).json()


def post(client: TestClient, headers: Headers, room_id: int, content: str) -> dict:
    res = client.post(f"/api/rooms/{room_id}/messages", json={"content": content}, headers=headers)
    assert res.status_code == 201
    return res.json()


def list_messages(client: TestClient, headers: Headers, room_id: int) -> list[dict]:
    return client.get(f"/api/rooms/{room_id}/messages", headers=headers).json()["messages"]


def user_messages(messages: list[dict]) -> list[dict]:
    """システムメッセージ（参加通知など）を除いた、ユーザーの投稿だけ。"""
    return [m for m in messages if m["kind"] in ("text", "image")]


# ---- WebSocket のヘルパー ----
def ws_token(headers: Headers) -> str:
    return headers["Authorization"].removeprefix("Bearer ")


def receive_by_type(ws, count: int) -> dict[str, dict]:
    """count 件のイベントを受信し、type ごとに引けるようにする（届く順序に依存しない）。"""
    events = [ws.receive_json() for _ in range(count)]
    return {event["type"]: event for event in events}
