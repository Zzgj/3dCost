def test_create_and_get_supplier(client):
    resp = client.post("/api/suppliers", json={"name": "淘宝-XX店"})
    assert resp.status_code == 200
    sid = resp.json()["data"]["id"]
    assert client.get(f"/api/suppliers/{sid}").json()["data"]["name"] == "淘宝-XX店"


def test_list_and_update_supplier(client):
    sid = client.post("/api/suppliers", json={"name": "A"}).json()["data"]["id"]
    client.patch(f"/api/suppliers/{sid}", json={"note": "备注"})
    assert client.get(f"/api/suppliers/{sid}").json()["data"]["note"] == "备注"
    assert client.get("/api/suppliers").json()["pagination"]["total"] == 1


def test_get_missing_supplier_returns_404(client):
    resp = client.get("/api/suppliers/999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"
