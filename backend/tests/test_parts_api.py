def test_create_and_get_part(client):
    resp = client.post("/api/parts", json={"name": "12V电源", "category": "电源"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "12V电源"
    assert data["conversion_ratio"] == "1.000"
    pid = data["id"]
    assert client.get(f"/api/parts/{pid}").json()["data"]["id"] == pid


def test_search_parts(client):
    client.post("/api/parts", json={"name": "12V电源", "category": "电源"})
    client.post("/api/parts", json={"name": "M3螺丝", "category": "螺丝"})
    resp = client.get("/api/parts?search=电源")
    body = resp.json()
    assert body["pagination"]["total"] == 1
    assert body["data"][0]["name"] == "12V电源"


def test_filter_parts_by_category(client):
    client.post("/api/parts", json={"name": "M3螺丝", "category": "螺丝"})
    client.post("/api/parts", json={"name": "M4螺丝", "category": "螺丝"})
    client.post("/api/parts", json={"name": "12V电源", "category": "电源"})
    resp = client.get("/api/parts?category=螺丝")
    assert resp.json()["pagination"]["total"] == 2


def test_get_missing_part_returns_404(client):
    resp = client.get("/api/parts/999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"
