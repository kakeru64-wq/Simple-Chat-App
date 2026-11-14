from tests.conftest import create_room


def _search(client, headers, q: str) -> list[str]:
    res = client.get("/api/rooms", params={"q": q}, headers=headers)
    assert res.status_code == 200
    return sorted(r["name"] for r in res.json())


def test_search_by_partial_name(client, alice):
    for name in ("映画部", "映画好き", "料理部"):
        create_room(client, alice, name)
    assert _search(client, alice, "映画") == ["映画好き", "映画部"]
    assert _search(client, alice, "部") == ["料理部", "映画部"]
    assert _search(client, alice, "テニス") == []


def test_search_is_case_insensitive(client, alice):
    create_room(client, alice, "Python Club")
    assert _search(client, alice, "python") == ["Python Club"]
    assert _search(client, alice, "CLUB") == ["Python Club"]


def test_search_treats_wildcards_literally(client, alice):
    for name in ("100%", "1000", "a_b", "axb", "c\\d"):
        create_room(client, alice, name)
    assert _search(client, alice, "%") == ["100%"]
    assert _search(client, alice, "_") == ["a_b"]
    assert _search(client, alice, "\\") == ["c\\d"]


def test_blank_query_returns_all_rooms(client, alice):
    create_room(client, alice, "a")
    create_room(client, alice, "b")
    assert _search(client, alice, "  ") == ["a", "b"]


def test_search_includes_rooms_not_joined(client, alice, bob):
    create_room(client, alice, "secret base")
    res = client.get("/api/rooms", params={"q": "secret"}, headers=bob).json()
    assert [(r["name"], r["is_member"]) for r in res] == [("secret base", False)]


def test_search_query_too_long_is_rejected(client, alice):
    res = client.get("/api/rooms", params={"q": "a" * 31}, headers=alice)
    assert res.status_code == 422
