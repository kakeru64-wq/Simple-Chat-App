def _general_id(client, headers) -> int:
    return client.get("/api/rooms", headers=headers).json()[0]["id"]


def test_post_and_list_messages(client, alice, bob):
    room_id = _general_id(client, alice)
    res = client.post(f"/api/rooms/{room_id}/messages", json={"content": "hi"}, headers=alice)
    assert res.status_code == 201
    assert res.json()["user"]["name"] == "alice"
    client.post(f"/api/rooms/{room_id}/messages", json={"content": "hello"}, headers=bob)

    body = client.get(f"/api/rooms/{room_id}/messages", headers=alice).json()
    assert [m["content"] for m in body["messages"]] == ["hi", "hello"]  # 古い順
    assert [m["user"]["name"] for m in body["messages"]] == ["alice", "bob"]
    assert body["has_more"] is False
    assert body["messages"][0]["created_at"].endswith("+00:00")


def test_messages_are_isolated_per_room(client, alice):
    general = _general_id(client, alice)
    other = client.post("/api/rooms", json={"name": "other"}, headers=alice).json()["id"]
    client.post(f"/api/rooms/{general}/messages", json={"content": "in general"}, headers=alice)

    body = client.get(f"/api/rooms/{other}/messages", headers=alice).json()
    assert body["messages"] == []


def test_pagination_with_before_id(client, alice):
    room_id = _general_id(client, alice)
    for i in range(5):
        client.post(f"/api/rooms/{room_id}/messages", json={"content": f"m{i}"}, headers=alice)

    latest = client.get(f"/api/rooms/{room_id}/messages?limit=2", headers=alice).json()
    assert [m["content"] for m in latest["messages"]] == ["m3", "m4"]
    assert latest["has_more"] is True

    before = latest["messages"][0]["id"]
    older = client.get(
        f"/api/rooms/{room_id}/messages?limit=2&before_id={before}", headers=alice
    ).json()
    assert [m["content"] for m in older["messages"]] == ["m1", "m2"]

    oldest = client.get(
        f"/api/rooms/{room_id}/messages?limit=2&before_id={older['messages'][0]['id']}",
        headers=alice,
    ).json()
    assert [m["content"] for m in oldest["messages"]] == ["m0"]
    assert oldest["has_more"] is False


def test_rejects_empty_or_too_long_message(client, alice):
    room_id = _general_id(client, alice)
    url = f"/api/rooms/{room_id}/messages"
    assert client.post(url, json={"content": "  \n "}, headers=alice).status_code == 422
    assert client.post(url, json={"content": "a" * 1001}, headers=alice).status_code == 422


def test_post_to_unknown_room_returns_404(client, alice):
    res = client.post("/api/rooms/9999/messages", json={"content": "hi"}, headers=alice)
    assert res.status_code == 404


def test_messages_require_auth(client, alice):
    room_id = _general_id(client, alice)
    assert client.get(f"/api/rooms/{room_id}/messages").status_code == 401
    res = client.post(f"/api/rooms/{room_id}/messages", json={"content": "hi"})
    assert res.status_code == 401
