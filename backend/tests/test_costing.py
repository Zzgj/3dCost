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


def test_product_cost_flat():
    """扁平BOM：打印件18.03 + 零件17.33 + 后处理0.8h*30=24 → subtotal=59.36; scrap5%=2.968; total=62.328(展示62.33); price=未舍入total*1.6=99.7248→99.72"""
    result = calc_product_cost(
        bom_items=[
            {"kind": "printitem", "unit_price": Decimal("18.03"), "qty": Decimal("1")},
            {"kind": "part", "unit_price": Decimal("17.33"), "qty": Decimal("1")},
            {"kind": "postprocess", "hours": Decimal("0.8")},
        ],
        markup_rate=Decimal("1.6"),
        labor_rate=Decimal("30"),
        scrap_rate=Decimal("0.05"),
    )
    assert result["printitems_cost"] == Decimal("18.03")
    assert result["parts_cost"] == Decimal("17.33")
    assert result["postprocess_cost"] == Decimal("24.00")
    assert result["subproduct_cost"] == Decimal("0.00")
    assert result["subtotal"] == Decimal("59.36")
    assert result["scrap_cost"] == Decimal("2.97")
    assert result["total_cost"] == Decimal("62.33")
    assert result["customer_price"] == Decimal("99.72")


def test_product_cost_with_subproduct():
    """含子产品：子total=50，2个→100；加零件10→subtotal110；scrap5%=5.5→total=115.5；*2=231"""
    result = calc_product_cost(
        bom_items=[
            {"kind": "subproduct", "unit_price": Decimal("50"), "qty": Decimal("2")},
            {"kind": "part", "unit_price": Decimal("10"), "qty": Decimal("1")},
        ],
        markup_rate=Decimal("2"),
        labor_rate=Decimal("30"),
        scrap_rate=Decimal("0.05"),
    )
    assert result["subproduct_cost"] == Decimal("100.00")
    assert result["parts_cost"] == Decimal("10.00")
    assert result["subtotal"] == Decimal("110.00")
    assert result["scrap_cost"] == Decimal("5.50")
    assert result["total_cost"] == Decimal("115.50")
    assert result["customer_price"] == Decimal("231.00")


def test_product_cost_zero_scrap():
    """废品率为0时无损耗"""
    result = calc_product_cost(
        bom_items=[{"kind": "part", "unit_price": Decimal("100"), "qty": Decimal("1")}],
        markup_rate=Decimal("1.5"),
        labor_rate=Decimal("30"),
        scrap_rate=Decimal("0"),
    )
    assert result["scrap_cost"] == Decimal("0.00")
    assert result["total_cost"] == Decimal("100.00")
    assert result["customer_price"] == Decimal("150.00")


def test_print_item_empty_filaments():
    """空 filaments：耗材成本为0，机时成本仍 > 0"""
    result = calc_print_item_cost(
        filaments=[],
        print_hours=Decimal("1"),
        machine_price=Decimal("7999"),
        machine_life_hours=10000,
        machine_power_w=350,
        electricity_price=Decimal("0.65"),
    )
    assert result["material_cost"] == Decimal("0.00")
    assert result["machine_cost"] > 0


def test_product_cost_empty_bom():
    """空 BOM：所有分项及汇总均为0"""
    result = calc_product_cost(
        bom_items=[],
        markup_rate=Decimal("1.6"),
        labor_rate=Decimal("30"),
        scrap_rate=Decimal("0.05"),
    )
    assert result["printitems_cost"] == Decimal("0.00")
    assert result["parts_cost"] == Decimal("0.00")
    assert result["postprocess_cost"] == Decimal("0.00")
    assert result["subproduct_cost"] == Decimal("0.00")
    assert result["subtotal"] == Decimal("0.00")
    assert result["scrap_cost"] == Decimal("0.00")
    assert result["total_cost"] == Decimal("0.00")
    assert result["customer_price"] == Decimal("0.00")


def test_product_cost_zero_qty():
    """零数量：part qty=0，parts_cost 为0"""
    result = calc_product_cost(
        bom_items=[{"kind": "part", "unit_price": Decimal("100"), "qty": Decimal("0")}],
        markup_rate=Decimal("1.6"),
        labor_rate=Decimal("30"),
        scrap_rate=Decimal("0.05"),
    )
    assert result["parts_cost"] == Decimal("0.00")
