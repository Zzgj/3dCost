from decimal import Decimal


def _seed_basics(client):
    """建机器、成本参数、耗材、打印件、零件，返回 (print_item_id, part_id)。"""
    client.patch(
        "/api/settings/cost",
        json={
            "electricity_price": "0.65",
            "scrap_rate": "0.05",
            "labor_rate": "30",
            "default_markup": "1.6",
        },
    )
    mac = client.post(
        "/api/machines",
        json={"name": "X1C", "price": "7999", "life_hours": 10000, "power_w": 350},
    ).json()["data"]["id"]
    mat = client.post("/api/materials", json={"name": "PLA黑", "type": "PLA"}).json()["data"]["id"]
    # 给耗材一个到手价：录入采购 2卷*1000g, 160+10元 → 0.085/g
    client.post(
        "/api/purchases",
        json={
            "target_kind": "material",
            "target_id": mat,
            "qty_rolls": 2,
            "grams_per_roll": 1000,
            "goods_amount": "160",
            "shipping_fee": "10",
        },
    )
    pi = client.post(
        "/api/print-items",
        json={
            "name": "件",
            "machine_id": mac,
            "print_hours": "1",
            "filaments": [{"material_id": mat, "grams": "200"}],
        },
    ).json()["data"]["id"]
    part = client.post("/api/parts", json={"name": "电源", "category": "电源"}).json()["data"]["id"]
    # 零件到手价：1个 13.33+4=17.33
    client.post(
        "/api/purchases",
        json={
            "target_kind": "part",
            "target_id": part,
            "qty": "1",
            "goods_amount": "13.33",
            "shipping_fee": "4",
        },
    )
    return pi, part


def test_create_product_returns_cost_tree(client):
    pi, part = _seed_basics(client)
    resp = client.post(
        "/api/products",
        json={
            "name": "成品",
            "mode": "estimate",
            "markup_rate": "1.6",
            "bom_items": [
                {"kind": "printitem", "ref_id": pi, "qty": "1"},
                {"kind": "part", "ref_id": part, "qty": "1"},
                {"kind": "postprocess", "hours": "0.8"},
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "draft"
    cd = data["cost_detail"]
    # 打印件: 200*0.085=17 + 机时1*(0.7999+0.2275)=1.03 → 18.03
    assert cd["printitems_cost"] == "18.03"
    assert cd["parts_cost"] == "17.33"
    assert cd["postprocess_cost"] == "24.00"
    assert cd["total_cost"] == data["total_cost"]
    assert len(data["bom_items"]) == 3
    # BOM 快照已落库
    pp = next(b for b in data["bom_items"] if b["kind"] == "printitem")
    assert pp["unit_price"] == "18.03"
    assert pp["subtotal"] == "18.03"


def test_get_product_detail(client):
    pi, part = _seed_basics(client)
    pid = client.post(
        "/api/products",
        json={"name": "P", "bom_items": [{"kind": "part", "ref_id": part, "qty": "2"}]},
    ).json()["data"]["id"]
    got = client.get(f"/api/products/{pid}")
    assert got.status_code == 200
    data = got.json()["data"]
    assert data["id"] == pid
    assert data["cost_detail"]["parts_cost"] == "34.66"  # 17.33*2


def test_list_products_filter_status(client):
    _seed_basics(client)
    client.post("/api/products", json={"name": "A"})
    client.post("/api/products", json={"name": "B"})
    resp = client.get("/api/products?status=draft")
    assert resp.json()["pagination"]["total"] == 2


def test_update_product_recomputes_cost(client):
    pi, part = _seed_basics(client)
    pid = client.post(
        "/api/products",
        json={"name": "P", "bom_items": [{"kind": "part", "ref_id": part, "qty": "1"}]},
    ).json()["data"]["id"]
    upd = client.patch(
        f"/api/products/{pid}",
        json={"bom_items": [{"kind": "part", "ref_id": part, "qty": "3"}]},
    )
    assert upd.json()["data"]["cost_detail"]["parts_cost"] == "51.99"  # 17.33*3


def test_get_missing_product_404(client):
    resp = client.get("/api/products/999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_create_product_with_cycle_returns_400(client):
    # A 引用 B，B 引用 A
    a = client.post("/api/products", json={"name": "A"}).json()["data"]["id"]
    b = client.post("/api/products", json={"name": "B"}).json()["data"]["id"]
    client.patch(
        f"/api/products/{a}",
        json={"bom_items": [{"kind": "subproduct", "ref_id": b, "qty": "1"}]},
    )
    resp = client.patch(
        f"/api/products/{b}",
        json={"bom_items": [{"kind": "subproduct", "ref_id": a, "qty": "1"}]},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "BOM_CYCLE_DETECTED"


def test_consume_stock_endpoint(client):
    pi, part = _seed_basics(client)
    pid = client.post(
        "/api/products",
        json={
            "name": "成品",
            "bom_items": [
                {"kind": "printitem", "ref_id": pi, "qty": "1"},
                {"kind": "part", "ref_id": part, "qty": "1"},
            ],
        },
    ).json()["data"]["id"]
    resp = client.post(f"/api/products/{pid}/consume-stock")
    assert resp.status_code == 200
    consumed = resp.json()["data"]["consumed"]
    assert len(consumed["materials"]) == 1
    assert len(consumed["parts"]) == 1
    # 耗材库存 2000 - 200 = 1800
    mat_list = client.get("/api/materials").json()["data"]
    assert mat_list[0]["stock_g"] == "1800.000"


def test_consume_stock_insufficient_returns_400(client):
    pi, part = _seed_basics(client)
    # 零件只买了1个，产品需要5个
    pid = client.post(
        "/api/products",
        json={"name": "成品", "bom_items": [{"kind": "part", "ref_id": part, "qty": "5"}]},
    ).json()["data"]["id"]
    resp = client.post(f"/api/products/{pid}/consume-stock")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_complete_locks_product(client):
    pi, part = _seed_basics(client)
    pid = client.post(
        "/api/products",
        json={"name": "P", "bom_items": [{"kind": "part", "ref_id": part, "qty": "1"}]},
    ).json()["data"]["id"]
    done = client.post(f"/api/products/{pid}/complete")
    assert done.status_code == 200
    assert done.json()["data"]["status"] == "completed"
    # 锁定后禁止修改
    upd = client.patch(f"/api/products/{pid}", json={"name": "改名"})
    assert upd.status_code == 409
    assert upd.json()["error"]["code"] == "LOCKED_RESOURCE"
