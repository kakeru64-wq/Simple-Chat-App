"""システムメッセージ（トーク名の変更・参加・退会の記録）"""

from tests.conftest import create_room, get_room, list_messages, post


# ---- トーク名の変更 ----
def test_rename_posts_system_message(client, alice, bob, room_id):
    post(client, alice, room_id, "hello")
    client.patch(f"/api/rooms/{room_id}", json={"name": "映画部"}, headers=bob)

    notice = list_messages(client, alice, room_id)[-1]
    assert notice["kind"] == "room_renamed"
    assert notice["content"] == "映画部"
    assert notice["user"]["name"] == "bob"
    # トーク一覧の最新メッセージにも出る
    assert get_room(client, alice, room_id)["last_message"]["kind"] == "room_renamed"


def test_rename_to_same_name_posts_nothing(client, alice, room_id):
    client.patch(f"/api/rooms/{room_id}", json={"name": "lobby"}, headers=alice)
    kinds = [m["kind"] for m in list_messages(client, alice, room_id)]
    assert "room_renamed" not in kinds


def test_rename_message_is_not_unread(client, alice, bob, room_id):
    client.patch(f"/api/rooms/{room_id}", json={"name": "renamed"}, headers=bob)
    assert get_room(client, alice, room_id)["unread_count"] == 0


def test_rename_message_cannot_be_deleted(client, alice, room_id):
    client.patch(f"/api/rooms/{room_id}", json={"name": "renamed"}, headers=alice)
    notice_id = list_messages(client, alice, room_id)[-1]["id"]
    res = client.delete(f"/api/rooms/{room_id}/messages/{notice_id}", headers=alice)
    assert res.status_code == 403


# ---- 参加・退会 ----
def test_join_and_leave_post_system_messages(client, alice, bob):
    room_id = create_room(client, alice, "club")
    client.put(f"/api/rooms/{room_id}/members/me", headers=bob)
    client.delete(f"/api/rooms/{room_id}/members/me", headers=bob)

    notices = [(m["kind"], m["user"]["name"]) for m in list_messages(client, alice, room_id)]
    assert notices == [("member_joined", "bob"), ("member_left", "bob")]
    assert get_room(client, alice, room_id)["last_message"]["kind"] == "member_left"


def test_creating_a_room_posts_no_join_message(client, alice):
    room_id = create_room(client, alice, "club")
    assert list_messages(client, alice, room_id) == []


def test_repeated_join_or_leave_posts_once(client, alice, bob):
    room_id = create_room(client, alice, "club")
    for _ in range(2):
        client.put(f"/api/rooms/{room_id}/members/me", headers=bob)
    for _ in range(2):
        client.delete(f"/api/rooms/{room_id}/members/me", headers=bob)
    kinds = [m["kind"] for m in list_messages(client, alice, room_id)]
    assert kinds == ["member_joined", "member_left"]


def test_join_and_leave_messages_are_not_unread(client, alice, bob):
    room_id = create_room(client, alice, "club")
    client.put(f"/api/rooms/{room_id}/members/me", headers=bob)
    client.delete(f"/api/rooms/{room_id}/members/me", headers=bob)
    assert get_room(client, alice, room_id)["unread_count"] == 0


def test_join_and_leave_messages_cannot_be_deleted(client, alice, bob):
    room_id = create_room(client, alice, "club")
    client.put(f"/api/rooms/{room_id}/members/me", headers=bob)
    notice_id = list_messages(client, bob, room_id)[-1]["id"]
    res = client.delete(f"/api/rooms/{room_id}/messages/{notice_id}", headers=bob)
    assert res.status_code == 403
