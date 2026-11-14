"""画像メッセージ（/api/rooms/{id}/messages/images と /uploads）"""

from tests.conftest import create_room, list_messages

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def _upload(client, headers, room_id, data: bytes):
    return client.post(
        f"/api/rooms/{room_id}/messages/images",
        files={"file": ("a.png", data, "image/png")},
        headers=headers,
    )


def test_upload_image_and_fetch_it(client, alice, room_id):
    res = _upload(client, alice, room_id, PNG_BYTES)
    assert res.status_code == 201
    body = res.json()
    assert body["kind"] == "image"
    assert body["content"] is None
    assert body["image_url"].startswith("/uploads/") and body["image_url"].endswith(".png")

    image = client.get(body["image_url"])
    assert image.status_code == 200
    assert image.content == PNG_BYTES


def test_upload_rejects_non_image_even_with_image_content_type(client, alice, room_id):
    res = _upload(client, alice, room_id, b"<script>alert(1)</script>")
    assert res.status_code == 415


def test_upload_rejects_too_large_image(client, alice, room_id):
    res = _upload(client, alice, room_id, PNG_BYTES + b"\x00" * 2048)
    assert res.status_code == 413


def test_upload_requires_membership(client, alice, bob):
    room_id = create_room(client, alice, "club")
    assert _upload(client, bob, room_id, PNG_BYTES).status_code == 403


def test_deleting_image_message_removes_file(client, alice, room_id):
    image_url = _upload(client, alice, room_id, PNG_BYTES).json()["image_url"]
    msg_id = list_messages(client, alice, room_id)[-1]["id"]
    res = client.delete(f"/api/rooms/{room_id}/messages/{msg_id}", headers=alice)
    assert res.json()["image_url"] is None
    assert client.get(image_url).status_code == 404
