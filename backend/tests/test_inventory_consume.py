from decimal import Decimal

import pytest

from app.models import BOMItem, Material, Part, PrintFilament, PrintItem, Product
from app.services.inventory import InsufficientStockError, consume_stock_for_product


def _seed(db):
    m = Material(
        name="PLA",
        type="PLA",
        stock_g=Decimal("1000"),
        low_stock_g=Decimal("100"),
        avg_price_per_g=Decimal("0.085"),
    )
    db.add(m)
    db.flush()
    pi = PrintItem(name="件", machine_id=1, print_hours=Decimal("1"))
    db.add(pi)
    db.flush()
    db.add(PrintFilament(print_item_id=pi.id, material_id=m.id, grams=Decimal("200")))
    db.flush()
    part = Part(
        name="电源",
        stock_qty=Decimal("5"),
        low_stock_qty=Decimal("2"),
        avg_unit_price=Decimal("17.33"),
    )
    db.add(part)
    db.flush()
    prod = Product(name="成品")
    db.add(prod)
    db.flush()
    db.add_all(
        [
            BOMItem(product_id=prod.id, kind="printitem", ref_id=pi.id, qty=Decimal("1")),
            BOMItem(product_id=prod.id, kind="part", ref_id=part.id, qty=Decimal("1")),
            BOMItem(product_id=prod.id, kind="postprocess", hours=Decimal("0.5")),
        ]
    )
    db.flush()
    return m, part, prod


def test_consume_deducts_material_and_part(db_session):
    db = db_session
    m, part, prod = _seed(db)
    result = consume_stock_for_product(db, prod)
    assert m.stock_g == Decimal("800.000")  # 1000 - 200
    assert part.stock_qty == Decimal("4.000")  # 5 - 1
    assert len(result["consumed"]["materials"]) == 1
    assert len(result["consumed"]["parts"]) == 1


def test_consume_low_stock_warning(db_session):
    db = db_session
    m, part, prod = _seed(db)
    part.stock_qty = Decimal("2")  # 扣1后=1 < 阈值2
    db.flush()
    result = consume_stock_for_product(db, prod)
    assert any("电源" in w for w in result["warnings"])


def test_consume_insufficient_material_rolls_back(db_session):
    db = db_session
    m, part, prod = _seed(db)
    m.stock_g = Decimal("100")  # 需要 200，不足
    db.flush()
    with pytest.raises(InsufficientStockError):
        consume_stock_for_product(db, prod)
    # 整体失败：零件库存未被扣减
    assert part.stock_qty == Decimal("5.000")
    assert m.stock_g == Decimal("100.000")


def test_consume_insufficient_part_rolls_back(db_session):
    db = db_session
    m, part, prod = _seed(db)
    part.stock_qty = Decimal("0")  # 零件不足
    db.flush()
    with pytest.raises(InsufficientStockError):
        consume_stock_for_product(db, prod)
    # 耗材未被扣减
    assert m.stock_g == Decimal("1000.000")


def test_consume_includes_subproduct_demands(db_session):
    db = db_session
    m, part, child = _seed(db)
    parent = Product(name="母件")
    db.add(parent)
    db.flush()
    db.add(BOMItem(product_id=parent.id, kind="subproduct", ref_id=child.id, qty=Decimal("1")))
    db.flush()

    result = consume_stock_for_product(db, parent)

    assert m.stock_g == Decimal("800.000")
    assert part.stock_qty == Decimal("4.000")
    assert result["consumed"]["materials"][0]["deducted_g"] == "200.000"
    assert result["consumed"]["parts"][0]["deducted_qty"] == "1.000"
