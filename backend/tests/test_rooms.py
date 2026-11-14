from tests.conftest import create_room, post


def _room(client, headers, room_id) -> dict:
    return client.get(f"/api/rooms/{room_id}", headers=headers).json()


def test_new_user_joins_default_room(client, alice):
    rooms = client.get("/api/rooms", headers=alice).json()
    assert [(r["name"], r["is_member"]) for r in rooms] == [("General", True)]


def test_rooms_require_auth(client):
    assert client.get("/api/rooms").status_code == 401


def test_create_room_makes_creator_a_member(client, alice, bob):
    room_id = create_room(client, alice, "random")
    assert _room(client, alice, room_id)["is_member"] is True
    assert _room(client, alice, room_id)["member_count"] == 1
    assert _room(client, bob, room_id)["is_member"] is False


def test_create_duplicate_room_conflicts(client, alice):
    assert client.post("/api/rooms", json={"name": "General"}, headers=alice).status_code == 409


def test_get_unknown_room_returns_404(client, alice):
    assert client.get("/api/rooms/9999", headers=alice).status_code == 404


def test_room_list_shows_last_message_and_sorts_by_activity(client, alice, general_id):
    other = create_room(client, alice, "other")
    post(client, alice, general_id, "older")
    post(client, alice, other, "newer")

    rooms = client.get("/api/rooms", headers=alice).json()
    assert [r["name"] for r in rooms] == ["other", "General"]
    assert rooms[0]["last_message"]["content"] == "newer"
    assert rooms[1]["last_message"]["content"] == "older"


def test_last_message_skips_deleted(client, alice, general_id):
    post(client, alice, general_id, "keep")
    latest = post(client, alice, general_id, "remove")
    client.delete(f"/api/rooms/{general_id}/messages/{latest['id']}", headers=alice)
    assert _room(client, alice, general_id)["last_message"]["content"] == "keep"
