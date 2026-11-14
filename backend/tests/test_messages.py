from tests.conftest import create_room, post

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def test_post_and_list_messages(client, alice, bob, room_id):
    first = post(client, alice, room_id, "hi")
    assert first["user"]["name"] == "alice"
    assert first["image_url"] is None
    assert first["is_deleted"] is False
    post(client, bob, room_id, "hello")

    body = client.get(f"/api/rooms/{room_id}/messages", headers=alice).json()
    assert [m["content"] for m in body["messages"]] == ["hi", "hello"]  # 古い順
    assert [m["user"]["name"] for m in body["messages"]] == ["alice", "bob"]
    assert body["has_more"] is False
    assert body["messages"][0]["created_at"].endswith("+00:00")


def test_messages_are_isolated_per_room(client, alice, room_id):
    other = create_room(client, alice, "other")
    post(client, alice, room_id, "in lobby")
    body = client.get(f"/api/rooms/{other}/messages", headers=alice).json()
    assert body["messages"] == []


def test_pagination_with_before_id(client, alice, room_id):
    for i in range(5):
        post(client, alice, room_id, f"m{i}")
    url = f"/api/rooms/{room_id}/messages"

    latest = client.get(f"{url}?limit=2", headers=alice).json()
    assert [m["content"] for m in latest["messages"]] == ["m3", "m4"]
    assert latest["has_more"] is True

    before = latest["messages"][0]["id"]
    older = client.get(f"{url}?limit=2&before_id={before}", headers=alice).json()
    assert [m["content"] for m in older["messages"]] == ["m1", "m2"]

    before = older["messages"][0]["id"]
    oldest = client.get(f"{url}?limit=2&before_id={before}", headers=alice).json()
    assert [m["content"] for m in oldest["messages"]] == ["m0"]
    assert oldest["has_more"] is False


def test_rejects_empty_or_too_long_message(client, alice, room_id):
    url = f"/api/rooms/{room_id}/messages"
    assert client.post(url, json={"content": "  \n "}, headers=alice).status_code == 422
    assert client.post(url, json={"content": "a" * 1001}, headers=alice).status_code == 422


def test_post_to_unknown_room_returns_404(client, alice):
    res = client.post("/api/rooms/9999/messages", json={"content": "hi"}, headers=alice)
    assert res.status_code == 404


def test_messages_require_auth(client, room_id):
    assert client.get(f"/api/rooms/{room_id}/messages").status_code == 401
    res = client.post(f"/api/rooms/{room_id}/messages", json={"content": "hi"})
    assert res.status_code == 401


# ---- 削除 ----
def test_delete_own_message(client, alice, room_id):
    msg = post(client, alice, room_id, "secret")
    res = client.delete(f"/api/rooms/{room_id}/messages/{msg['id']}", headers=alice)
    assert res.status_code == 200
    assert res.json()["is_deleted"] is True
    assert res.json()["content"] is None

    # 履歴には「取り消し」として位置が残る
    listed = client.get(f"/api/rooms/{room_id}/messages", headers=alice).json()["messages"]
    assert [(m["id"], m["is_deleted"], m["content"]) for m in listed] == [(msg["id"], True, None)]


def test_cannot_delete_others_message(client, alice, bob, room_id):
    msg = post(client, alice, room_id, "mine")
    res = client.delete(f"/api/rooms/{room_id}/messages/{msg['id']}", headers=bob)
    assert res.status_code == 403


def test_delete_message_in_wrong_room_returns_404(client, alice, room_id):
    other = create_room(client, alice, "other")
    msg = post(client, alice, room_id, "x")
    res = client.delete(f"/api/rooms/{other}/messages/{msg['id']}", headers=alice)
    assert res.status_code == 404


# ---- 画像 ----
def _upload(client, headers, room_id, data: bytes, filename="a.png", content_type="image/png"):
    return client.post(
        f"/api/rooms/{room_id}/messages/images",
        files={"file": (filename, data, content_type)},
        headers=headers,
    )


def test_upload_image_and_fetch_it(client, alice, room_id):
    res = _upload(client, alice, room_id, PNG_BYTES)
    assert res.status_code == 201
    body = res.json()
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
    msg_id = client.get(f"/api/rooms/{room_id}/messages", headers=alice).json()["messages"][-1][
        "id"
    ]
    res = client.delete(f"/api/rooms/{room_id}/messages/{msg_id}", headers=alice)
    assert res.json()["image_url"] is None
    assert client.get(image_url).status_code == 404
