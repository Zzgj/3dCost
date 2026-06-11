def test_get_cost_settings_returns_defaults(client):
    resp = client.get("/api/settings/cost")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["scrap_rate"] == "0.0500"
    assert data["default_markup"] == "1.6000"


def test_update_cost_settings(client):
    resp = client.patch("/api/settings/cost", json={"electricity_price": "0.8", "labor_rate": "40"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["electricity_price"] == "0.8000"
    assert data["labor_rate"] == "40.0000"
    # 再次 GET 确认持久化
    assert client.get("/api/settings/cost").json()["data"]["electricity_price"] == "0.8000"
