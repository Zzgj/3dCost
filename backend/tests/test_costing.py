from decimal import Decimal
from app.services.costing import calc_print_item_cost, calc_product_cost


def test_print_item_single_material():
    """单色：200g PLA @ 0.085/g = 17.00 耗材；1h机时(折旧0.7999+电费0.2275)=1.03"""
    result = calc_print_item_cost(
        filaments=[(Decimal("200"), Decimal("0.085"))],
        print_hours=Decimal("1"),
        machine_price=Decimal("7999"),
        machine_life_hours=10000,
        machine_power_w=350,
        electricity_price=Decimal("0.65"),
    )
    assert result["material_cost"] == Decimal("17.00")
    assert result["machine_cost"] == Decimal("1.03")
    assert result["total"] == Decimal("18.03")


def test_print_item_multicolor():
    """多色：200g@0.085 + 58g@0.1 = 17+5.8=22.8"""
    result = calc_print_item_cost(
        filaments=[(Decimal("200"), Decimal("0.085")), (Decimal("58"), Decimal("0.1"))],
        print_hours=Decimal("2"),
        machine_price=Decimal("7999"),
        machine_life_hours=10000,
        machine_power_w=350,
        electricity_price=Decimal("0.65"),
    )
    assert result["material_cost"] == Decimal("22.80")
    assert result["machine_cost"] == Decimal("2.05")
    assert result["total"] == Decimal("24.85")


def test_print_item_zero_hours():
    """0小时打印（仅耗材成本）"""
    result = calc_print_item_cost(
        filaments=[(Decimal("100"), Decimal("0.1"))],
        print_hours=Decimal("0"),
        machine_price=Decimal("5000"),
        machine_life_hours=10000,
        machine_power_w=300,
        electricity_price=Decimal("0.6"),
    )
    assert result["material_cost"] == Decimal("10.00")
    assert result["machine_cost"] == Decimal("0.00")
    assert result["total"] == Decimal("10.00")
