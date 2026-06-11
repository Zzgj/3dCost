def test_create_and_get_machine(client):
    resp = client.post("/api/machines", json={"name": "X1C", "price": "7999", "life_hours": 10000, "power_w": 350})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "X1C"
    assert data["life_hours"] == 10000
    mid = data["id"]
    assert client.get(f"/api/machines/{mid}").json()["data"]["id"] == mid


def test_update_machine(client):
    mid = client.post("/api/machines", json={"name": "P1S", "price": "5000", "life_hours": 8000, "power_w": 300}).json()["data"]["id"]
    client.patch(f"/api/machines/{mid}", json={"power_w": 320})
    assert client.get(f"/api/machines/{mid}").json()["data"]["power_w"] == 320


def test_invalid_life_hours_rejected(client):
    resp = client.post("/api/machines", json={"name": "Bad", "price": "1", "life_hours": 0, "power_w": 1})
    assert resp.status_code == 422


def test_get_missing_machine_returns_404(client):
    resp = client.get("/api/machines/999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"
