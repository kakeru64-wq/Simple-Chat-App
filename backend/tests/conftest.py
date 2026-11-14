import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

# app をインポートする前にテスト用 DB を指定する
_tmpdir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmpdir) / 'test.db'}"
os.environ["UPLOAD_DIR"] = str(Path(_tmpdir) / "uploads")
os.environ["MAX_IMAGE_BYTES"] = "1024"  # テストで上限超過を試しやすくする

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:  # lifespan でテーブル作成とデフォルトルーム投入
        yield c


def login(client: TestClient, name: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"name": name})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['token']}"}


@pytest.fixture
def alice(client: TestClient) -> dict[str, str]:
    return login(client, "alice")


@pytest.fixture
def bob(client: TestClient) -> dict[str, str]:
    return login(client, "bob")


@pytest.fixture
def room_id(client: TestClient, alice: dict[str, str], bob: dict[str, str]) -> int:
    """alice が作成し、bob も参加しているルーム。"""
    room_id = create_room(client, alice, "lobby")
    assert client.put(f"/api/rooms/{room_id}/members/me", headers=bob).status_code == 200
    return room_id


def create_room(client: TestClient, headers: dict[str, str], name: str) -> int:
    res = client.post("/api/rooms", json={"name": name}, headers=headers)
    assert res.status_code == 201
    return res.json()["id"]


def post(client: TestClient, headers: dict[str, str], room_id: int, content: str) -> dict:
    res = client.post(f"/api/rooms/{room_id}/messages", json={"content": content}, headers=headers)
    assert res.status_code == 201
    return res.json()
