from tests.conftest import create_room, post


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


def test_join_and_leave_are_idempotent(client, alice, room_id):
    assert client.put(f"/api/rooms/{room_id}/members/me", headers=alice).status_code == 200
    assert client.put(f"/api/rooms/{room_id}/members/me", headers=alice).status_code == 200
    assert _room(client, alice, room_id)["member_count"] == 2
    assert client.delete(f"/api/rooms/{room_id}/members/me", headers=alice).status_code == 204
    assert client.delete(f"/api/rooms/{room_id}/members/me", headers=alice).status_code == 204


def test_join_unknown_room_returns_404(client, alice):
    assert client.put("/api/rooms/9999/members/me", headers=alice).status_code == 404


def test_unread_count_and_mark_read(client, alice, bob, room_id):
    post(client, alice, room_id, "1")
    post(client, alice, room_id, "2")
    last = post(client, alice, room_id, "3")
    post(client, bob, room_id, "own message is not unread")

    assert _room(client, bob, room_id)["unread_count"] == 3
    assert _room(client, alice, room_id)["unread_count"] == 1

    res = client.put(f"/api/rooms/{room_id}/read", json={"message_id": last["id"]}, headers=bob)
    assert res.status_code == 204
    assert _room(client, bob, room_id)["unread_count"] == 0


def test_mark_read_never_moves_backwards(client, alice, bob, room_id):
    first = post(client, alice, room_id, "1")
    second = post(client, alice, room_id, "2")
    url = f"/api/rooms/{room_id}/read"
    client.put(url, json={"message_id": second["id"]}, headers=bob)
    client.put(url, json={"message_id": first["id"]}, headers=bob)
    assert _room(client, bob, room_id)["unread_count"] == 0


def test_deleted_messages_are_not_unread(client, alice, bob, room_id):
    msg = post(client, alice, room_id, "oops")
    client.delete(f"/api/rooms/{room_id}/messages/{msg['id']}", headers=alice)
    assert _room(client, bob, room_id)["unread_count"] == 0


def test_history_before_joining_is_not_unread(client, alice, bob):
    room_id = create_room(client, alice, "club")
    post(client, alice, room_id, "before bob joined")
    client.put(f"/api/rooms/{room_id}/members/me", headers=bob)
    assert _room(client, bob, room_id)["unread_count"] == 0
    post(client, alice, room_id, "after")
    assert _room(client, bob, room_id)["unread_count"] == 1


# ---- 参加・退会のシステムメッセージ ----
def _messages(client, headers, room_id) -> list[dict]:
    return client.get(f"/api/rooms/{room_id}/messages", headers=headers).json()["messages"]


def test_join_and_leave_post_system_messages(client, alice, bob):
    room_id = create_room(client, alice, "club")
    client.put(f"/api/rooms/{room_id}/members/me", headers=bob)
    client.delete(f"/api/rooms/{room_id}/members/me", headers=bob)

    notices = [(m["kind"], m["user"]["name"]) for m in _messages(client, alice, room_id)]
    assert notices == [("member_joined", "bob"), ("member_left", "bob")]
    assert _room(client, alice, room_id)["last_message"]["kind"] == "member_left"


def test_creating_a_room_posts_no_join_message(client, alice):
    room_id = create_room(client, alice, "club")
    assert _messages(client, alice, room_id) == []


def test_repeated_join_or_leave_posts_once(client, alice, bob):
    room_id = create_room(client, alice, "club")
    for _ in range(2):
        client.put(f"/api/rooms/{room_id}/members/me", headers=bob)
    for _ in range(2):
        client.delete(f"/api/rooms/{room_id}/members/me", headers=bob)
    kinds = [m["kind"] for m in _messages(client, alice, room_id)]
    assert kinds == ["member_joined", "member_left"]


def test_join_and_leave_messages_are_not_unread(client, alice, bob):
    room_id = create_room(client, alice, "club")
    client.put(f"/api/rooms/{room_id}/members/me", headers=bob)
    client.delete(f"/api/rooms/{room_id}/members/me", headers=bob)
    assert _room(client, alice, room_id)["unread_count"] == 0


def test_join_and_leave_messages_cannot_be_deleted(client, alice, bob):
    room_id = create_room(client, alice, "club")
    client.put(f"/api/rooms/{room_id}/members/me", headers=bob)
    notice_id = _messages(client, bob, room_id)[-1]["id"]
    res = client.delete(f"/api/rooms/{room_id}/messages/{notice_id}", headers=bob)
    assert res.status_code == 403
