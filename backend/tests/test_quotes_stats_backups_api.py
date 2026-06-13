import app.services.backups as backup_service
from datetime import datetime

from tests.test_products_api import _seed_basics


def test_quote_snapshot_and_export(client):
    _, part = _seed_basics(client)
    product_id = client.post(
        "/api/products",
        json={"name": "报价产品", "bom_items": [{"kind": "part", "ref_id": part, "qty": "1"}]},
    ).json()["data"]["id"]

    created = client.post("/api/quotes", json={"product_id": product_id})

    assert created.status_code == 200
    quote = created.json()["data"]
    assert quote["snapshot"]["product"]["name"] == "报价产品"
    assert quote["internal_cost"] == quote["snapshot"]["cost_detail"]["total_cost"]

    listed = client.get(f"/api/quotes?product_id={product_id}")
    assert listed.status_code == 200
    assert listed.json()["pagination"]["total"] == 1

    html = client.get(f"/api/quotes/{quote['id']}/export?type=internal&format=html")
    assert html.status_code == 200
    assert "内部报价单" in html.text


def test_stats_low_stock_and_monthly(client):
    _, part = _seed_basics(client)
    product_id = client.post(
        "/api/products",
        json={"name": "统计产品", "bom_items": [{"kind": "part", "ref_id": part, "qty": "1"}]},
    ).json()["data"]["id"]
    client.post(f"/api/products/{product_id}/complete")
    client.patch(f"/api/parts/{part}", json={"low_stock_qty": "2"})

    low = client.get("/api/stats/low-stock")
    assert low.status_code == 200
    assert low.json()["data"]["parts"][0]["name"] == "电源"

    now = datetime.utcnow()
    monthly = client.get(f"/api/stats/monthly?year={now.year}&month={now.month}")
    assert monthly.status_code == 200
    assert monthly.json()["data"]["products_count"] == 1
    assert monthly.json()["data"]["completed_count"] == 1


def test_backup_list_endpoint(client, monkeypatch, tmp_path):
    backup_file = tmp_path / "3dcost-test.db"
    backup_file.write_text("backup")
    monkeypatch.setattr(backup_service, "BACKUP_DIR", tmp_path)

    listed = client.get("/api/backups")

    assert listed.status_code == 200
    assert listed.json()["data"][0]["filename"] == "3dcost-test.db"
