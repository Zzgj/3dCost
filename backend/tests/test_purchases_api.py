def _make_material(client):
    return client.post("/api/materials", json={"name": "PLA黑", "type": "PLA"}).json()["data"]["id"]


def _make_part(client):
    return client.post(
        "/api/parts",
        json={
            "name": "12V电源",
            "category": "电源",
            "purchase_unit": "个",
            "use_unit": "个",
            "conversion_ratio": "1",
        },
    ).json()["data"]["id"]


def test_material_purchase_updates_stock_and_price(client):
    mid = _make_material(client)
    # 2卷 * 1000g, 货款160 + 运费10 = 170 → 0.085/g
    resp = client.post(
        "/api/purchases",
        json={
            "target_kind": "material",
            "target_id": mid,
            "qty_rolls": 2,
            "grams_per_roll": 1000,
            "goods_amount": "160",
            "shipping_fee": "10",
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_stock"] == "2000.000"
    assert data["updated_avg_price"] == "0.0850"

    mat = client.get(f"/api/materials/{mid}").json()["data"]
    assert mat["stock_g"] == "2000.000"
    assert mat["avg_price_per_g"] == "0.0850"


def test_part_purchase_power_example_weighted_avg(client):
    pid = _make_part(client)
    # 第1批: 1个, 货款16 + 运费4 = 20
    client.post(
        "/api/purchases",
        json={
            "target_kind": "part", "target_id": pid,
            "qty": "1", "goods_amount": "16", "shipping_fee": "4",
        },
    )
    # 第2批: 2个, 货款28 + 运费4 = 32 → (20+32)/3 = 17.3333
    resp = client.post(
        "/api/purchases",
        json={
            "target_kind": "part", "target_id": pid,
            "qty": "2", "goods_amount": "28", "shipping_fee": "4",
        },
    )
    data = resp.json()["data"]
    assert data["total_stock"] == "3.000"
    assert data["updated_avg_price"] == "17.3333"


def test_purchase_missing_target_returns_404(client):
    resp = client.post(
        "/api/purchases",
        json={"target_kind": "material", "target_id": 999,
              "qty_rolls": 1, "grams_per_roll": 1000, "goods_amount": "80"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_material_purchase_requires_roll_fields(client):
    mid = _make_material(client)
    resp = client.post(
        "/api/purchases",
        json={"target_kind": "material", "target_id": mid, "goods_amount": "80"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_purchases_for_target(client):
    mid = _make_material(client)
    client.post(
        "/api/purchases",
        json={"target_kind": "material", "target_id": mid,
              "qty_rolls": 1, "grams_per_roll": 1000, "goods_amount": "80"},
    )
    resp = client.get(f"/api/purchases?target_kind=material&target_id={mid}")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1
