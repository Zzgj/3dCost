def _make_machine(client):
    return client.post(
        "/api/machines",
        json={"name": "X1C", "price": "7999", "life_hours": 10000, "power_w": 350},
    ).json()["data"]["id"]


def _make_material(client, price_per_g):
    mid = client.post("/api/materials", json={"name": "PLA黑", "type": "PLA"}).json()["data"]["id"]
    client.post(
        "/api/purchases",
        json={
            "target_kind": "material", "target_id": mid,
            "qty_rolls": 1, "grams_per_roll": 1000,
            "goods_amount": str(price_per_g * 1000), "shipping_fee": "0",
        },
    )
    return mid


def test_create_print_item_returns_cost(client):
    machine_id = _make_machine(client)
    mid = _make_material(client, 0.085)
    resp = client.post(
        "/api/print-items",
        json={
            "name": "小型排风机", "machine_id": machine_id,
            "print_hours": "2", "plates": 4, "nozzle": "0.4mm",
            "filaments": [{"material_id": mid, "grams": "100"}],
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "小型排风机"
    assert len(data["filaments"]) == 1
    assert data["cost"]["material_cost"] == "8.50"
    assert data["cost"]["machine_cost"] == "2.05"
    assert data["cost"]["total"] == "10.55"


def test_get_print_item_includes_cost(client):
    machine_id = _make_machine(client)
    mid = _make_material(client, 0.085)
    pid = client.post(
        "/api/print-items",
        json={"name": "件A", "machine_id": machine_id, "print_hours": "2",
              "filaments": [{"material_id": mid, "grams": "100"}]},
    ).json()["data"]["id"]
    got = client.get(f"/api/print-items/{pid}")
    assert got.status_code == 200
    assert got.json()["data"]["cost"]["total"] == "10.55"


def test_update_print_item_recomputes_cost(client):
    machine_id = _make_machine(client)
    mid = _make_material(client, 0.085)
    pid = client.post(
        "/api/print-items",
        json={"name": "件A", "machine_id": machine_id, "print_hours": "2",
              "filaments": [{"material_id": mid, "grams": "100"}]},
    ).json()["data"]["id"]
    upd = client.patch(
        f"/api/print-items/{pid}",
        json={"filaments": [{"material_id": mid, "grams": "200"}]},
    )
    assert upd.json()["data"]["cost"]["material_cost"] == "17.00"
    assert upd.json()["data"]["cost"]["total"] == "19.05"


def test_list_print_items(client):
    machine_id = _make_machine(client)
    mid = _make_material(client, 0.085)
    for i in range(2):
        client.post(
            "/api/print-items",
            json={"name": f"件{i}", "machine_id": machine_id, "print_hours": "1",
                  "filaments": [{"material_id": mid, "grams": "50"}]},
        )
    resp = client.get("/api/print-items")
    assert resp.json()["pagination"]["total"] == 2


def test_get_missing_print_item_returns_404(client):
    resp = client.get("/api/print-items/999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_create_with_missing_machine_returns_400_and_no_dirty_row(client):
    # 机器不存在：创建应返回 400 COST_SOURCE_MISSING，且不落库脏数据
    mid = _make_material(client, 0.085)

    # 先确认初始列表为空
    initial_count = client.get("/api/print-items").json()["pagination"]["total"]

    # 尝试创建（机器不存在）
    resp = client.post(
        "/api/print-items",
        json={"name": "坏件", "machine_id": 999, "print_hours": "1",
              "filaments": [{"material_id": mid, "grams": "50"}]},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "COST_SOURCE_MISSING"

    # 确认列表数量未增加（未落库）
    final_count = client.get("/api/print-items").json()["pagination"]["total"]
    assert final_count == initial_count


def test_cost_uses_default_settings_without_writing_settings(client):
    # 未创建成本参数时，成本用默认电价 0.65 算出；且只读路径不应写出 settings 行
    machine_id = _make_machine(client)
    mid = _make_material(client, 0.085)
    pid = client.post(
        "/api/print-items",
        json={"name": "件A", "machine_id": machine_id, "print_hours": "2",
              "filaments": [{"material_id": mid, "grams": "100"}]},
    ).json()["data"]["id"]
    # 默认电价 0.65 → machine_cost 2.05, total 10.55
    assert client.get(f"/api/print-items/{pid}").json()["data"]["cost"]["total"] == "10.55"
    # GET 成本设置应返回默认值（若之前被写脏会暴露），electricity_price 仍是默认 0.65
    assert client.get("/api/settings/cost").json()["data"]["electricity_price"] == "0.6500"


def test_list_degrades_when_machine_deactivated(client):
    # 列表中某打印件的机器被停用，整页仍可返回，该件 cost 降级为 null
    machine_id = _make_machine(client)
    mid = _make_material(client, 0.085)
    client.post(
        "/api/print-items",
        json={"name": "件A", "machine_id": machine_id, "print_hours": "1",
              "filaments": [{"material_id": mid, "grams": "50"}]},
    )
    # 软删除机器（停用），制造成本来源失效
    client.patch(f"/api/machines/{machine_id}", json={"is_active": False})
    resp = client.get("/api/print-items")
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] == 1
    item = resp.json()["data"][0]
    assert item["cost"] is None
    assert item["cost_error"] == "COST_SOURCE_MISSING"
