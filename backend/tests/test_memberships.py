from tests.conftest import create_room, login, post


def _room(client, headers, room_id) -> dict:
    return client.get(f"/api/rooms/{room_id}", headers=headers).json()


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
    assert _room(client, bob, room_id)["is_member"] is False
    assert _room(client, bob, room_id)["member_count"] == 1
    assert client.get(f"/api/rooms/{room_id}/messages", headers=bob).status_code == 403


def test_join_and_leave_are_idempotent(client, alice, general_id):
    assert client.put(f"/api/rooms/{general_id}/members/me", headers=alice).status_code == 200
    assert client.put(f"/api/rooms/{general_id}/members/me", headers=alice).status_code == 200
    assert _room(client, alice, general_id)["member_count"] == 1
    assert client.delete(f"/api/rooms/{general_id}/members/me", headers=alice).status_code == 204
    assert client.delete(f"/api/rooms/{general_id}/members/me", headers=alice).status_code == 204


def test_join_unknown_room_returns_404(client, alice):
    assert client.put("/api/rooms/9999/members/me", headers=alice).status_code == 404


def test_unread_count_and_mark_read(client, alice, bob, general_id):
    post(client, alice, general_id, "1")
    post(client, alice, general_id, "2")
    last = post(client, alice, general_id, "3")
    post(client, bob, general_id, "own message is not unread")

    assert _room(client, bob, general_id)["unread_count"] == 3
    assert _room(client, alice, general_id)["unread_count"] == 1

    res = client.put(f"/api/rooms/{general_id}/read", json={"message_id": last["id"]}, headers=bob)
    assert res.status_code == 204
    assert _room(client, bob, general_id)["unread_count"] == 0


def test_mark_read_never_moves_backwards(client, alice, bob, general_id):
    first = post(client, alice, general_id, "1")
    second = post(client, alice, general_id, "2")
    url = f"/api/rooms/{general_id}/read"
    client.put(url, json={"message_id": second["id"]}, headers=bob)
    client.put(url, json={"message_id": first["id"]}, headers=bob)
    assert _room(client, bob, general_id)["unread_count"] == 0


def test_deleted_messages_are_not_unread(client, alice, bob, general_id):
    msg = post(client, alice, general_id, "oops")
    client.delete(f"/api/rooms/{general_id}/messages/{msg['id']}", headers=alice)
    assert _room(client, bob, general_id)["unread_count"] == 0


def test_history_before_joining_is_not_unread(client, alice, bob):
    room_id = create_room(client, alice, "club")
    post(client, alice, room_id, "before bob joined")
    client.put(f"/api/rooms/{room_id}/members/me", headers=bob)
    assert _room(client, bob, room_id)["unread_count"] == 0
    post(client, alice, room_id, "after")
    assert _room(client, bob, room_id)["unread_count"] == 1


def test_new_user_does_not_see_old_default_room_history_as_unread(client, alice, general_id):
    post(client, alice, general_id, "before carol signed up")
    carol = login(client, "carol")
    assert _room(client, carol, general_id)["unread_count"] == 0
