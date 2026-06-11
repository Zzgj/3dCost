def test_create_and_get_material(client):
    resp = client.post("/api/materials", json={"name": "拓竹PLA黑", "type": "PLA"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "拓竹PLA黑"
    assert data["stock_g"] == "0.000"
    mid = data["id"]
    got = client.get(f"/api/materials/{mid}")
    assert got.status_code == 200
    assert got.json()["data"]["id"] == mid


def test_list_materials_pagination(client):
    for i in range(3):
        client.post("/api/materials", json={"name": f"M{i}", "type": "PLA"})
    resp = client.get("/api/materials?page=1&page_size=2")
    body = resp.json()
    assert len(body["data"]) == 2
    assert body["pagination"]["total"] == 3


def test_update_and_soft_delete_material(client):
    mid = client.post("/api/materials", json={"name": "X", "type": "PLA"}).json()["data"]["id"]
    upd = client.patch(f"/api/materials/{mid}", json={"brand": "拓竹"})
    assert upd.json()["data"]["brand"] == "拓竹"
    client.delete(f"/api/materials/{mid}")
    assert client.get("/api/materials").json()["pagination"]["total"] == 0


def test_get_missing_material_returns_404(client):
    resp = client.get("/api/materials/999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"
