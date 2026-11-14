import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

# app をインポートする前にテスト用 DB を指定する
_tmpdir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmpdir) / 'test.db'}"

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
