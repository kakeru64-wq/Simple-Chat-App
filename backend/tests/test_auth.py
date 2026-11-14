"""ログイン・現在のユーザー・ログアウト（/api/auth）"""

from tests.conftest import login


def test_login_creates_user_and_returns_token(client):
    res = client.post("/api/auth/login", json={"name": "  alice  "})
    assert res.status_code == 200
    body = res.json()
    assert body["token"]
    assert body["user"]["name"] == "alice"  # 前後の空白は除去される


def test_login_with_existing_name_returns_same_user(client):
    first = client.post("/api/auth/login", json={"name": "alice"}).json()
    second = client.post("/api/auth/login", json={"name": "alice"}).json()
    assert first["user"]["id"] == second["user"]["id"]
    assert first["token"] != second["token"]


def test_login_rejects_invalid_name(client):
    assert client.post("/api/auth/login", json={"name": "   "}).status_code == 422
    assert client.post("/api/auth/login", json={"name": "a" * 21}).status_code == 422


def test_me_requires_valid_token(client):
    assert client.get("/api/auth/me").status_code == 401
    bad = {"Authorization": "Bearer invalid"}
    assert client.get("/api/auth/me", headers=bad).status_code == 401


def test_me_returns_current_user(client):
    headers = login(client, "alice")
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "alice"


def test_logout_invalidates_token(client):
    headers = login(client, "alice")
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401
