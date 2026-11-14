def test_default_room_exists(client, alice):
    rooms = client.get("/api/rooms", headers=alice).json()
    assert [r["name"] for r in rooms] == ["General"]


def test_rooms_require_auth(client):
    assert client.get("/api/rooms").status_code == 401


def test_create_room(client, alice):
    res = client.post("/api/rooms", json={"name": "random"}, headers=alice)
    assert res.status_code == 201
    room = res.json()
    assert client.get(f"/api/rooms/{room['id']}", headers=alice).json()["name"] == "random"


def test_create_duplicate_room_conflicts(client, alice):
    assert client.post("/api/rooms", json={"name": "General"}, headers=alice).status_code == 409


def test_get_unknown_room_returns_404(client, alice):
    assert client.get("/api/rooms/9999", headers=alice).status_code == 404
