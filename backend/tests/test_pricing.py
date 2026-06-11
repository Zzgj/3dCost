from decimal import Decimal

from app.services.pricing import (
    material_total_grams,
    part_total_use_qty,
    weighted_avg_price,
)


def test_weighted_avg_price_power_example():
    # 第1批: 货款16 + 运费4 = 20, 数量1 → 20/个
    # 第2批: 货款28 + 运费4 = 32, 数量2
    # 加权平均 = (20 + 32) / (1 + 2) = 17.3333 → 量化到 4 位
    price = weighted_avg_price(
        total_amount=Decimal("52"), total_qty=Decimal("3")
    )
    assert price == Decimal("17.3333")


def test_weighted_avg_price_zero_qty_returns_zero():
    assert weighted_avg_price(Decimal("10"), Decimal("0")) == Decimal("0")


def test_material_total_grams():
    # 2卷 * 1000g + 1卷 * 500g = 2500g
    rows = [(2, 1000), (1, 500)]
    assert material_total_grams(rows) == Decimal("2500")


def test_part_total_use_qty():
    # 3盒 * 100个/盒 + 2盒 * 100 = 500个
    rows = [(Decimal("3"), Decimal("100")), (Decimal("2"), Decimal("100"))]
    assert part_total_use_qty(rows) == Decimal("500")
