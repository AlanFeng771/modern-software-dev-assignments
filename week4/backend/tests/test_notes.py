def test_create_and_list_notes(client):
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"

    r = client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get("/notes/search")
    assert r.status_code == 200

    r = client.get("/notes/search", params={"q": "Hello"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1


def test_search_notes_case_insensitive(client):
    client.post("/notes/", json={"title": "Grocery List", "content": "Buy Milk and Eggs"})

    r = client.get("/notes/search", params={"q": "grocery"})
    assert r.status_code == 200
    assert any(n["title"] == "Grocery List" for n in r.json())

    r = client.get("/notes/search", params={"q": "MILK"})
    assert r.status_code == 200
    assert any(n["title"] == "Grocery List" for n in r.json())


def test_search_notes_no_match(client):
    client.post("/notes/", json={"title": "Grocery List", "content": "Buy Milk and Eggs"})

    r = client.get("/notes/search", params={"q": "nonexistent-term"})
    assert r.status_code == 200
    assert r.json() == []


def test_search_notes_escapes_like_wildcards(client):
    client.post("/notes/", json={"title": "Discount", "content": "Save 50% today"})
    client.post("/notes/", json={"title": "Other", "content": "Nothing special here"})

    r = client.get("/notes/search", params={"q": "50%"})
    assert r.status_code == 200
    items = r.json()
    assert [n["title"] for n in items] == ["Discount"]

    r = client.get("/notes/search", params={"q": "_"})
    assert r.status_code == 200
    assert r.json() == []
