import pytest
from starlette.websockets import WebSocketDisconnect


def _token(headers: dict[str, str]) -> str:
    return headers["Authorization"].removeprefix("Bearer ")


def test_posted_message_is_broadcast_to_room(client, alice, bob):
    room_id = client.get("/api/rooms", headers=alice).json()[0]["id"]

    with client.websocket_connect(f"/ws/rooms/{room_id}?token={_token(bob)}") as ws:
        client.post(f"/api/rooms/{room_id}/messages", json={"content": "hey"}, headers=alice)
        event = ws.receive_json()

    assert event["type"] == "message.created"
    assert event["message"]["content"] == "hey"
    assert event["message"]["user"]["name"] == "alice"


def test_broadcast_is_scoped_to_room(client, alice):
    general = client.get("/api/rooms", headers=alice).json()[0]["id"]
    other = client.post("/api/rooms", json={"name": "other"}, headers=alice).json()["id"]

    with client.websocket_connect(f"/ws/rooms/{other}?token={_token(alice)}") as ws:
        client.post(f"/api/rooms/{general}/messages", json={"content": "x"}, headers=alice)
        client.post(f"/api/rooms/{other}/messages", json={"content": "y"}, headers=alice)
        # other ルームの購読者には other のメッセージだけが届く
        assert ws.receive_json()["message"]["content"] == "y"


def test_websocket_rejects_invalid_token(client, alice):
    room_id = client.get("/api/rooms", headers=alice).json()[0]["id"]
    with (
        client.websocket_connect(f"/ws/rooms/{room_id}?token=bad") as ws,
        pytest.raises(WebSocketDisconnect) as exc,
    ):
        ws.receive_json()
    assert exc.value.code == 4401


def test_websocket_rejects_unknown_room(client, alice):
    with (
        client.websocket_connect(f"/ws/rooms/9999?token={_token(alice)}") as ws,
        pytest.raises(WebSocketDisconnect) as exc,
    ):
        ws.receive_json()
    assert exc.value.code == 4404
