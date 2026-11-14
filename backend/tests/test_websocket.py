import pytest
from starlette.websockets import WebSocketDisconnect

from tests.conftest import create_room, post


def _token(headers: dict[str, str]) -> str:
    return headers["Authorization"].removeprefix("Bearer ")


def test_posted_message_is_sent_to_room_members(client, alice, bob, room_id):
    with client.websocket_connect(f"/ws?token={_token(bob)}") as ws:
        post(client, alice, room_id, "hey")
        event = ws.receive_json()

    assert event["type"] == "message.created"
    assert event["message"]["room_id"] == room_id
    assert event["message"]["content"] == "hey"
    assert event["message"]["user"]["name"] == "alice"


def test_events_are_only_sent_to_members(client, alice, bob, room_id):
    club = create_room(client, alice, "club")  # bob は未参加

    with client.websocket_connect(f"/ws?token={_token(bob)}") as ws:
        post(client, alice, club, "members only")
        post(client, alice, room_id, "for everyone")
        # bob には参加中の lobby のメッセージだけが届く
        assert ws.receive_json()["message"]["content"] == "for everyone"


def test_left_member_stops_receiving(client, alice, bob, room_id):
    client.delete(f"/api/rooms/{room_id}/members/me", headers=bob)
    club = create_room(client, bob, "club")
    client.put(f"/api/rooms/{club}/members/me", headers=alice)

    with client.websocket_connect(f"/ws?token={_token(bob)}") as ws:
        post(client, alice, room_id, "bob left lobby")
        post(client, alice, club, "still in club")
        assert ws.receive_json()["message"]["content"] == "still in club"


def test_deleted_message_event(client, alice, bob, room_id):
    msg = post(client, alice, room_id, "oops")
    with client.websocket_connect(f"/ws?token={_token(bob)}") as ws:
        client.delete(f"/api/rooms/{room_id}/messages/{msg['id']}", headers=alice)
        event = ws.receive_json()

    assert event["type"] == "message.deleted"
    assert event["message"]["id"] == msg["id"]
    assert event["message"]["is_deleted"] is True


def test_websocket_rejects_invalid_token(client):
    with (
        client.websocket_connect("/ws?token=bad") as ws,
        pytest.raises(WebSocketDisconnect) as exc,
    ):
        ws.receive_json()
    assert exc.value.code == 4401


def test_rename_is_sent_to_members(client, alice, bob, room_id):
    with client.websocket_connect(f"/ws?token={_token(bob)}") as ws:
        client.patch(f"/api/rooms/{room_id}", json={"name": "renamed"}, headers=alice)
        updated = ws.receive_json()
        notice = ws.receive_json()
    assert updated == {"type": "room.updated", "room": {"id": room_id, "name": "renamed"}}
    assert notice["type"] == "message.created"
    assert notice["message"]["kind"] == "room_renamed"
    assert notice["message"]["content"] == "renamed"
    assert notice["message"]["user"]["name"] == "alice"
