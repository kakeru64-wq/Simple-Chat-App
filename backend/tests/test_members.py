"""参加・退会・既読と未読数（/api/rooms/{id}/members/me, /read）"""

from tests.conftest import create_room, get_room, post


def test_non_member_cannot_read_or_post(client, alice, bob):
    room_id = create_room(client, alice, "private-ish")
    assert client.get(f"/api/rooms/{room_id}/messages", headers=bob).status_code == 403
    res = client.post(f"/api/rooms/{room_id}/messages", json={"content": "hi"}, headers=bob)
    assert res.status_code == 403


def test_join_and_leave(client, alice, bob):
    room_id = create_room(client, alice, "club")

    res = client.put(f"/api/rooms/{room_id}/members/me", headers=bob)
    assert res.status_code == 200
    assert res.json()["is_member"] is True
    assert res.json()["member_count"] == 2
    assert client.get(f"/api/rooms/{room_id}/messages", headers=bob).status_code == 200

    assert client.delete(f"/api/rooms/{room_id}/members/me", headers=bob).status_code == 204
    assert get_room(client, bob, room_id)["is_member"] is False
    assert get_room(client, bob, room_id)["member_count"] == 1
    assert client.get(f"/api/rooms/{room_id}/messages", headers=bob).status_code == 403


def test_join_and_leave_are_idempotent(client, alice, room_id):
    assert client.put(f"/api/rooms/{room_id}/members/me", headers=alice).status_code == 200
    assert client.put(f"/api/rooms/{room_id}/members/me", headers=alice).status_code == 200
    assert get_room(client, alice, room_id)["member_count"] == 2
    assert client.delete(f"/api/rooms/{room_id}/members/me", headers=alice).status_code == 204
    assert client.delete(f"/api/rooms/{room_id}/members/me", headers=alice).status_code == 204


def test_join_unknown_room_returns_404(client, alice):
    assert client.put("/api/rooms/9999/members/me", headers=alice).status_code == 404


# ---- 未読数と既読 ----
def test_unread_count_and_mark_read(client, alice, bob, room_id):
    post(client, alice, room_id, "1")
    post(client, alice, room_id, "2")
    last = post(client, alice, room_id, "3")
    post(client, bob, room_id, "own message is not unread")

    assert get_room(client, bob, room_id)["unread_count"] == 3
    assert get_room(client, alice, room_id)["unread_count"] == 1

    res = client.put(f"/api/rooms/{room_id}/read", json={"message_id": last["id"]}, headers=bob)
    assert res.status_code == 204
    assert get_room(client, bob, room_id)["unread_count"] == 0


def test_mark_read_never_moves_backwards(client, alice, bob, room_id):
    first = post(client, alice, room_id, "1")
    second = post(client, alice, room_id, "2")
    url = f"/api/rooms/{room_id}/read"
    client.put(url, json={"message_id": second["id"]}, headers=bob)
    client.put(url, json={"message_id": first["id"]}, headers=bob)
    assert get_room(client, bob, room_id)["unread_count"] == 0


def test_deleted_messages_are_not_unread(client, alice, bob, room_id):
    msg = post(client, alice, room_id, "oops")
    client.delete(f"/api/rooms/{room_id}/messages/{msg['id']}", headers=alice)
    assert get_room(client, bob, room_id)["unread_count"] == 0


def test_history_before_joining_is_not_unread(client, alice, bob):
    room_id = create_room(client, alice, "club")
    post(client, alice, room_id, "before bob joined")
    client.put(f"/api/rooms/{room_id}/members/me", headers=bob)
    assert get_room(client, bob, room_id)["unread_count"] == 0
    post(client, alice, room_id, "after")
    assert get_room(client, bob, room_id)["unread_count"] == 1
