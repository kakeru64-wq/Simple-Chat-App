"""ルームの一覧・作成・取得・名前変更（/api/rooms）"""

from tests.conftest import create_room, get_room, post


def test_no_rooms_initially(client, alice):
    assert client.get("/api/rooms", headers=alice).json() == []


def test_rooms_require_auth(client):
    assert client.get("/api/rooms").status_code == 401


def test_create_room_makes_creator_a_member(client, alice, bob):
    room_id = create_room(client, alice, "random")
    assert get_room(client, alice, room_id)["is_member"] is True
    assert get_room(client, alice, room_id)["member_count"] == 1
    assert get_room(client, bob, room_id)["is_member"] is False


def test_create_duplicate_room_conflicts(client, alice):
    create_room(client, alice, "dup")
    assert client.post("/api/rooms", json={"name": "dup"}, headers=alice).status_code == 409


def test_get_unknown_room_returns_404(client, alice):
    assert client.get("/api/rooms/9999", headers=alice).status_code == 404


def test_room_list_shows_last_message_and_sorts_by_activity(client, alice, room_id):
    other = create_room(client, alice, "other")
    post(client, alice, room_id, "older")
    post(client, alice, other, "newer")

    rooms = client.get("/api/rooms", headers=alice).json()
    assert [r["name"] for r in rooms] == ["other", "lobby"]
    assert rooms[0]["last_message"]["content"] == "newer"
    assert rooms[1]["last_message"]["content"] == "older"


def test_last_message_skips_deleted(client, alice, room_id):
    post(client, alice, room_id, "keep")
    latest = post(client, alice, room_id, "remove")
    client.delete(f"/api/rooms/{room_id}/messages/{latest['id']}", headers=alice)
    assert get_room(client, alice, room_id)["last_message"]["content"] == "keep"


# ---- 名前変更 ----
def test_member_can_rename_room(client, alice, bob, room_id):
    res = client.patch(f"/api/rooms/{room_id}", json={"name": "  新しい名前 "}, headers=bob)
    assert res.status_code == 200
    assert res.json()["name"] == "新しい名前"
    assert get_room(client, alice, room_id)["name"] == "新しい名前"


def test_non_member_cannot_rename_room(client, alice, bob):
    room = create_room(client, alice, "club")
    assert client.patch(f"/api/rooms/{room}", json={"name": "x"}, headers=bob).status_code == 403


def test_rename_to_existing_name_conflicts(client, alice, room_id):
    create_room(client, alice, "taken")
    res = client.patch(f"/api/rooms/{room_id}", json={"name": "taken"}, headers=alice)
    assert res.status_code == 409


def test_rename_to_same_name_is_ok(client, alice, room_id):
    res = client.patch(f"/api/rooms/{room_id}", json={"name": "lobby"}, headers=alice)
    assert res.status_code == 200


def test_rename_validation_and_not_found(client, alice, room_id):
    url = f"/api/rooms/{room_id}"
    assert client.patch(url, json={"name": "  "}, headers=alice).status_code == 422
    assert client.patch(url, json={"name": "a" * 31}, headers=alice).status_code == 422
    assert client.patch("/api/rooms/9999", json={"name": "x"}, headers=alice).status_code == 404
